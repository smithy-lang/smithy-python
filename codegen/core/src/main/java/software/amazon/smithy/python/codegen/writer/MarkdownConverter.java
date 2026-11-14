/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.Reader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Converts CommonMark/HTML documentation to Markdown for Python docstrings.
 *
 * This converter uses the pandoc CLI tool to convert documentation from CommonMark/HTML
 * format to Markdown suitable for Python docstrings with Google-style formatting.
 * Conversions share the generation's {@link PandocWorker} when it is available.
 *
 * Pandoc must be installed and available.
 */
@SmithyInternalApi
public final class MarkdownConverter {

    private static final int PANDOC_WRAP_COLUMNS = 72;
    private static final int TIMEOUT_SECONDS = 10;

    // List of HTML tags to exclude from documentation (including their content).
    private static final List<String> EXCLUDED_TAGS = List.of("fullname");

    // Private constructor to prevent instantiation
    private MarkdownConverter() {}

    /**
     * Converts HTML or CommonMark strings to Markdown format using pandoc.
     *
     * For AWS services, documentation is in HTML format with raw HTML tags.
     * For generic services, documentation is in CommonMark format which can
     * include embedded HTML.
     *
     * <p>The result is plain Markdown, for files such as the README. Nothing in it
     * is escaped for a Python string, and nothing is escaped for a writer either:
     * it is literal text, to be written with {@code $L} and not as a format string.
     *
     * @param input The input string (HTML or CommonMark)
     * @param context The generation context to determine service type
     * @return Markdown formatted string
     */
    public static String convert(String input, GenerationContext context) {
        return convert(input, context, false);
    }

    /**
     * Converts documentation like {@link #convert}, but to the contents of a
     * triple-quoted Python docstring: backslashes are escaped so that the string
     * compiles and decodes to the documentation, and so are quotes that would close
     * the docstring.
     *
     * <p>Use this for docstrings and {@link #convert} for plain Markdown output
     * such as the README, where the escaping would show up as literal backslashes.
     * Like that of {@link #convert}, the result is not escaped for a writer.
     *
     * @param input The input string (HTML or CommonMark)
     * @param context The generation context to determine service type
     * @return Markdown formatted string that is safe to embed in a docstring
     */
    public static String convertForDocstring(String input, GenerationContext context) {
        return escapeDocstringQuotes(convert(input, context, true));
    }

    private static String convert(String input, GenerationContext context, boolean forDocstring) {
        if (input == null || input.isEmpty()) {
            return "";
        }
        return convert(input, context, forDocstring, context.pandocWorker());
    }

    /**
     * Converts documentation like {@link #convert(String, GenerationContext)} with the
     * given worker, or with a separate pandoc process per conversion if it is null.
     */
    static String convert(String input, GenerationContext context, PandocWorker worker) {
        return convert(input, context, false, worker);
    }

    private static String convert(
            String input,
            GenerationContext context,
            boolean forDocstring,
            PandocWorker worker
    ) {
        if (input == null || input.isEmpty()) {
            return "";
        }

        try {
            input = preProcessPandocInput(input);

            if (!CodegenUtils.isAwsService(context)) {
                // Commonmark may include embedded HTML so we first normalize the input to HTML format
                input = convertWithPandoc(input, "commonmark", "html", worker);
            }

            // Null if there is no backslash to protect, and then none is put back.
            String codeBackslash = input.indexOf('\\') < 0 ? null : unusedPrivateUseCharacter(input);
            if (codeBackslash != null) {
                input = protectCodeBackslashes(input, codeBackslash);
            }

            // The "html+raw_html" format preserves unrecognized html tags (e.g. <note>, <important>)
            // in Markdown output. We convert these tags to admonitions in postProcressPandocOutput()
            String output = convertWithPandoc(input, "html+raw_html", "markdown", worker);

            return postProcessPandocOutput(output, codeBackslash, forDocstring);
        } catch (IOException | InterruptedException e) {
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            throw new CodegenException("Failed to convert documentation using pandoc: " + e.getMessage(), e);
        }
    }

    // The private-use characters that may stand in for a backslash of code while
    // the documentation goes through pandoc. They mean nothing to pandoc.
    private static final char FIRST_CODE_BACKSLASH = 0xE05C;
    private static final char LAST_CODE_BACKSLASH = 0xF8FF;
    private static final Pattern CODE_ELEMENT = Pattern.compile(
            "<(code|pre)\\b[^>]*>.*?</\\1\\s*>",
            Pattern.CASE_INSENSITIVE | Pattern.DOTALL);
    private static final Pattern TAG_OR_BACKSLASH = Pattern.compile("</?[A-Za-z][^>]*>|\\\\");

    /**
     * Picks the character that stands in for the backslashes of code in some HTML.
     *
     * <p>It must not be a character of the documentation, or putting the
     * backslashes back would make a backslash of that character too. Documentation
     * can write a character out or give it as a numeric character reference, which
     * pandoc decodes, so both are looked for. No named reference is a private-use
     * character. The choice depends on the HTML alone: it is the first such
     * character from U+E05C on that the HTML does not have.
     *
     * @param html The HTML to be converted by pandoc
     * @return The character, or null if the HTML has every one of them
     */
    private static String unusedPrivateUseCharacter(String html) {
        for (char candidate = FIRST_CODE_BACKSLASH; candidate <= LAST_CODE_BACKSLASH; candidate++) {
            if (html.indexOf(candidate) < 0 && !hasCharacterReference(html, candidate)) {
                return String.valueOf(candidate);
            }
        }
        return null;
    }

    private static boolean hasCharacterReference(String html, char character) {
        // Hexadecimal or decimal, with any leading zeros and with or without the
        // semicolon, but not the start of the reference to some larger number.
        return html.contains("&#") && Pattern.compile(
                "&#(?:x0*" + Integer.toHexString(character) + "(?![0-9a-f])|0*" + (int) character + "(?![0-9]))",
                Pattern.CASE_INSENSITIVE).matcher(html).find();
    }

    /**
     * Marks the backslashes of code so they can be told apart in pandoc's output.
     *
     * <p>Pandoc writes code verbatim, so a backslash in it is a literal one: of a
     * Windows path, a regular expression, an escape in some other language. Every
     * other backslash in its output is part of a Markdown escape. Once both are
     * Markdown the two look the same, and {@code \U} or a backslash before a closing
     * backtick cannot be read correctly. In the HTML that pandoc is given, code is
     * still marked up, so its backslashes are replaced here and put back, escaped
     * for where they are going, in {@link #postProcessPandocOutput}.
     *
     * @param html The HTML to be converted by pandoc
     * @param codeBackslash The character to replace them with, which the HTML does
     *     not have (see {@link #unusedPrivateUseCharacter})
     * @return The HTML with the backslashes in the text of code elements replaced
     */
    private static String protectCodeBackslashes(String html, String codeBackslash) {
        return CODE_ELEMENT.matcher(html)
                .replaceAll(element -> Matcher.quoteReplacement(
                        // Tags are matched so that they are skipped: only text is code.
                        TAG_OR_BACKSLASH.matcher(element.group())
                                .replaceAll(match -> match.group().equals("\\")
                                        ? codeBackslash
                                        : Matcher.quoteReplacement(match.group()))));
    }

    /**
     * Pre-processes input before passing to pandoc.
     *
     * @param input The raw input text
     * @return Pre-processed input ready for pandoc conversion
     */
    private static String preProcessPandocInput(String input) {
        // Trim leading and trailing spaces in hrefs i.e href=" https://example.com "
        Pattern p = Pattern.compile("href\\s*=\\s*\"([^\"]*)\"");
        input = p.matcher(input).replaceAll(match -> "href=\"" + match.group(1).trim() + "\"");

        // Remove excluded HTML tags and their content
        for (String tagName : EXCLUDED_TAGS) {
            input = removeHtmlTag(input, tagName);
        }

        return input;
    }

    /**
     * Removes HTML tags and their content from the input string
     *
     * @param text The text to process
     * @param tagName The tag name to remove (e.g., "fullname")
     * @return Text with tags and their content removed
     */
    private static String removeHtmlTag(String text, String tagName) {
        // Remove <tag>content</tag> completely
        Pattern p = Pattern.compile(
                "<" + Pattern.quote(tagName) + ">[\\s\\S]*?</" + Pattern.quote(tagName) + ">");
        return p.matcher(text).replaceAll("");
    }

    /**
     * Converts documentation with the generation's pandoc worker, falling back to the
     * pandoc CLI when there is no worker or the worker cannot reproduce the CLI's result.
     *
     * @param input The input string
     * @param fromFormat The input format (e.g., "html+raw_html" or "commonmark")
     * @param toFormat The output format (e.g., "markdown")
     * @param worker The generation's pandoc worker, or null
     * @return Converted string, with lines read the same way for either path
     * @throws IOException if process I/O fails
     * @throws InterruptedException if process is interrupted
     */
    private static String convertWithPandoc(String input, String fromFormat, String toFormat, PandocWorker worker)
            throws IOException, InterruptedException {
        if (worker != null) {
            Optional<String> output = worker.convert(input, fromFormat, toFormat);
            if (output.isPresent()) {
                return readLines(new StringReader(output.get()));
            }
        }
        return convertWithPandocCli(input, fromFormat, toFormat);
    }

    /**
     * Calls pandoc CLI to convert documentation.
     *
     * @param input The input string
     * @param fromFormat The input format (e.g., "html+raw_html" or "commonmark")
     * @param toFormat The output format (e.g., "markdown")
     * @return Converted Markdown string
     * @throws IOException if process I/O fails
     * @throws InterruptedException if process is interrupted
     */
    private static String convertWithPandocCli(String input, String fromFormat, String toFormat)
            throws IOException, InterruptedException {
        List<String> command = List.of(
                "pandoc",
                "--from=" + fromFormat,
                "--to=" + toFormat,
                "--wrap=auto",
                "--columns=" + PANDOC_WRAP_COLUMNS);
        return convertWithPandocCli(command, input, Duration.ofSeconds(TIMEOUT_SECONDS));
    }

    /**
     * Runs one pandoc command line conversion under a deadline.
     *
     * <p>The deadline covers the whole exchange: writing stdin, reading stdout and
     * stderr, and waiting for the exit. Input is written while output is read, so
     * neither can fill its pipe and stall the other. The process is stopped whenever
     * this returns without it having exited.
     *
     * @param command The command to run.
     * @param input The document to write to its stdin.
     * @param timeout The deadline for the whole exchange.
     * @return Its merged stdout and stderr, read line by line.
     * @throws IOException if process I/O fails
     * @throws InterruptedException if interrupted while waiting for the process
     */
    static String convertWithPandocCli(List<String> command, String input, Duration timeout)
            throws IOException, InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        ExecutorService io = Executors.newFixedThreadPool(2, MarkdownConverter::newDaemonThread);
        try {
            byte[] bytes = input.getBytes(StandardCharsets.UTF_8);
            Future<Void> writer = io.submit(() -> {
                try (OutputStream stdin = process.getOutputStream()) {
                    stdin.write(bytes);
                }
                return null;
            });
            Future<String> reader = io.submit(
                    () -> readLines(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8)));

            String output = await(reader, deadline);
            if (!process.waitFor(remaining(deadline), TimeUnit.NANOSECONDS)) {
                throw new TimeoutException();
            }
            int exitCode = process.exitValue();
            if (exitCode != 0) {
                // Reported before any write failure: pandoc may exit without reading all of its input.
                throw new CodegenException(
                        "Pandoc failed with exit code " + exitCode + ": " + output.trim());
            }
            await(writer, deadline);
            return output;
        } catch (TimeoutException e) {
            throw new CodegenException("Pandoc process timed out after " + timeout.toSeconds() + " seconds");
        } finally {
            if (process.isAlive()) {
                // Kill without closing the pipes, whose locks a blocked helper may hold.
                // Killing the process and anything it started breaks the pipes, which
                // ends both helpers.
                process.descendants().forEach(ProcessHandle::destroyForcibly);
                process.toHandle().destroyForcibly();
            }
            io.shutdownNow();
        }
    }

    private static <T> T await(Future<T> future, long deadline)
            throws IOException, InterruptedException, TimeoutException {
        try {
            return future.get(remaining(deadline), TimeUnit.NANOSECONDS);
        } catch (ExecutionException e) {
            if (e.getCause() instanceof IOException) {
                throw (IOException) e.getCause();
            }
            throw new CodegenException("Pandoc process I/O failed: " + e.getCause(), e.getCause());
        }
    }

    private static long remaining(long deadline) {
        return Math.max(0, deadline - System.nanoTime());
    }

    private static Thread newDaemonThread(Runnable runnable) {
        Thread thread = new Thread(runnable, "smithy-python-pandoc-cli");
        thread.setDaemon(true);
        return thread;
    }

    /**
     * Reads text line by line, ending every line with "\n".
     */
    private static String readLines(Reader source) throws IOException {
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(source)) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }
        return output.toString();
    }

    /**
     * Post-processes pandoc output into plain Markdown or the contents of a docstring.
     *
     * @param output The raw output from pandoc
     * @param codeBackslash The character that stands in for the backslashes of
     *     code, or null if none were replaced
     * @param forDocstring Whether backslashes are escaped for a Python string
     * @return Post-processed Markdown
     */
    private static String postProcessPandocOutput(String output, String codeBackslash, boolean forDocstring) {
        // Remove empty lines at the start and end
        output = output.trim();

        // Fix up the backslash escapes pandoc adds for Markdown (see
        // normalizeBackslashEscapes). The backslashes of code are not among them yet.
        output = normalizeBackslashEscapes(output, forDocstring);

        // Put the backslashes of code back. Markdown code is verbatim; in a Python
        // string each one is doubled, so that it decodes to itself whatever follows.
        if (codeBackslash != null) {
            output = output.replace(codeBackslash, forDocstring ? "\\\\" : "\\");
        }

        // Replace <note> and <important> tags with admonitions for mkdocstrings
        output = replaceAdmonitionTags(output, "note", "Note");
        return replaceAdmonitionTags(output, "important", "Warning");
    }

    // A lone backslash before one of these is dropped: pandoc adds it for Markdown
    // but the documentation reads better without it.
    private static final String MARKDOWN_ONLY_CHARS = "[](){}<>`@_*|!~$#^'.";
    // In a docstring, a lone backslash before one of these is kept: together they
    // form a valid Python escape. (' is intentionally left out; it lives in
    // MARKDOWN_ONLY_CHARS.)
    private static final String VALID_ESCAPE_CHARS = "\\\"abfnrtv01234567xNuU\r\n";
    private static final Pattern BACKSLASH_RUN = Pattern.compile("(\\\\+)([^\\\\]|$)", Pattern.DOTALL);

    /**
     * Fixes the backslash escaping that pandoc adds for Markdown.
     *
     * <p>Pandoc escapes literal backslashes and Markdown characters separately,
     * and adjacent escapes pile up into runs. For each run we keep the pairs. A
     * leftover backslash is dropped if it is only there for a Markdown character.
     * Otherwise plain Markdown keeps it as pandoc wrote it. A docstring must also
     * be a valid Python literal, so there it is kept only if it forms a valid
     * escape and is doubled if it does not.
     */
    private static String normalizeBackslashEscapes(String output, boolean forDocstring) {
        Matcher m = BACKSLASH_RUN.matcher(output);
        StringBuilder sb = new StringBuilder();
        while (m.find()) {
            int runLength = m.group(1).length();
            String next = m.group(2);
            int backslashes = (runLength / 2) * 2;
            if (runLength % 2 != 0) {
                char c = next.isEmpty() ? '\0' : next.charAt(0);
                if (forDocstring && !next.isEmpty() && VALID_ESCAPE_CHARS.indexOf(c) >= 0) {
                    backslashes += 1;
                } else if (next.isEmpty() || MARKDOWN_ONLY_CHARS.indexOf(c) < 0) {
                    backslashes += forDocstring ? 2 : 1;
                }
                // else: Markdown-only char, drop the spurious backslash
            }
            m.appendReplacement(sb, Matcher.quoteReplacement("\\".repeat(backslashes) + next));
        }
        m.appendTail(sb);
        return sb.toString();
    }

    private static final Pattern QUOTE_RUN = Pattern.compile("(\\\\*)(\"+)");

    /**
     * Escapes quotes that would otherwise close a triple-quoted docstring.
     *
     * <p>Pandoc leaves quotes in code verbatim, so a run of three or more
     * unescaped quotes would end the docstring early, and quotes at the very
     * end would run into its closing delimiter. Those quotes are escaped;
     * shorter runs are left alone. A quote after an odd backslash run is
     * already escaped and does not count toward a run.
     */
    private static String escapeDocstringQuotes(String output) {
        Matcher m = QUOTE_RUN.matcher(output);
        StringBuilder sb = new StringBuilder();
        while (m.find()) {
            String backslashes = m.group(1);
            String quotes = m.group(2);
            if (backslashes.length() % 2 != 0) {
                backslashes += "\"";
                quotes = quotes.substring(1);
            }
            if (quotes.length() >= 3 || (!quotes.isEmpty() && m.end() == output.length())) {
                quotes = quotes.replace("\"", "\\\"");
            }
            m.appendReplacement(sb, Matcher.quoteReplacement(backslashes + quotes));
        }
        m.appendTail(sb);
        return sb.toString();
    }

    // A line that is not the text of a paragraph: it is indented (code, or the body
    // of an admonition), or opens or rules off some other block (a list item, heading,
    // quote, table, definition, fence, reference, or raw HTML that is not an autolink).
    private static final Pattern NOT_PARAGRAPH_TEXT = Pattern.compile("^(?:"
            + "[ \\t]"
            + "|[-+*](?:\\s|$)"
            + "|\\(?(?:\\d+|[A-Za-z]|[ivx]+|[IVX]+|#|@\\w*)[.)](?:\\s|$)"
            + "|#{1,6}(?:\\s|$)"
            + "|[>|:]"
            + "|```|~~~"
            + "|\\[[^\\]]*\\]:"
            + "|<(?![A-Za-z][A-Za-z0-9+.-]*:)"
            + "|[-=+|:*_~`\\s]+$"
            + ")");
    // A backslash that ends a line is a hard line break, and escapes the newline in
    // a docstring.
    private static final Pattern ENDS_WITH_LINE_BREAK = Pattern.compile("(?<!\\\\)(?:\\\\\\\\)*\\\\$");

    /**
     * Finds the paragraph that opens converted documentation.
     *
     * <p>Pandoc hard-wraps paragraphs, so the first line of converted documentation
     * usually ends mid-sentence. A caller that needs the whole paragraph on one line
     * may join the lines up to the returned index with spaces, which does not change
     * what the Markdown means. That holds for a paragraph only, so anything else that
     * opens the documentation (a list, code, a table, an admonition, raw HTML) is
     * reported as not being one, as is a paragraph with a hard line break in it.
     *
     * @param markdown Documentation converted by {@link #convert} or
     *     {@link #convertForDocstring}.
     * @return The index of the end of the opening paragraph, exclusive of its final
     *     newline, or -1 if the documentation does not open with a paragraph.
     */
    public static int leadParagraphEnd(String markdown) {
        int end = 0;
        while (end < markdown.length()) {
            int newline = markdown.indexOf('\n', end);
            String line = markdown.substring(end, newline < 0 ? markdown.length() : newline);
            if (line.isBlank()) {
                break;
            }
            if (NOT_PARAGRAPH_TEXT.matcher(line).find() || ENDS_WITH_LINE_BREAK.matcher(line).find()) {
                return -1;
            }
            if (newline < 0) {
                return markdown.length();
            }
            end = newline + 1;
        }
        // Up to, and not including, the newline that ends the paragraph's last line.
        return end == 0 ? -1 : end - 1;
    }

    /**
     * Replaces admonition tags (e.g. note, important) with Google-style format.
     *
     * @param text The text to process
     * @param tagName The tag name to replace (e.g., "note", "important")
     * @param label The label to use (e.g., "Note", "Warning")
     * @return Text with replaced admonitions
     */
    private static String replaceAdmonitionTags(String text, String tagName, String label) {
        // Match <tag>content</tag> across multiple lines
        Pattern pattern = Pattern.compile("<" + tagName + ">\\s*([\\s\\S]*?)\\s*</" + tagName + ">");
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();

        while (matcher.find()) {
            // Extract the content between tags
            String content = matcher.group(1).trim();

            // Indent each line with 4 spaces
            String[] lines = content.split("\n");
            StringBuilder indented = new StringBuilder(label + ":\n");
            for (String line : lines) {
                indented.append("    ").append(line.trim()).append("\n");
            }

            matcher.appendReplacement(result, Matcher.quoteReplacement(indented.toString().trim()));
        }
        matcher.appendTail(result);

        return result.toString();
    }
}
