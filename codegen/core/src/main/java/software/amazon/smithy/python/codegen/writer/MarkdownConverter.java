/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.TimeUnit;
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
     * @param input The input string (HTML or CommonMark)
     * @param context The generation context to determine service type
     * @return Markdown formatted string
     */
    public static String convert(String input, GenerationContext context) {
        if (input == null || input.isEmpty()) {
            return "";
        }

        try {
            input = preProcessPandocInput(input);

            if (!CodegenUtils.isAwsService(context)) {
                // Commonmark may include embedded HTML so we first normalize the input to HTML format
                input = convertWithPandoc(input, "commonmark", "html");
            }

            // The "html+raw_html" format preserves unrecognized html tags (e.g. <note>, <important>)
            // in Markdown output. We convert these tags to admonitions in postProcressPandocOutput()
            String output = convertWithPandoc(input, "html+raw_html", "markdown");

            return postProcessPandocOutput(output);
        } catch (IOException | InterruptedException e) {
            throw new CodegenException("Failed to convert documentation using pandoc: " + e.getMessage(), e);
        }
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
     * Calls pandoc CLI to convert documentation.
     *
     * @param input The input string
     * @param fromFormat The input format (e.g., "html+raw_html" or "commonmark")
     * @param toFormat The output format (e.g., "markdown")
     * @return Converted Markdown string
     * @throws IOException if process I/O fails
     * @throws InterruptedException if process is interrupted
     */
    private static String convertWithPandoc(String input, String fromFormat, String toFormat)
            throws IOException, InterruptedException {
        ProcessBuilder processBuilder = new ProcessBuilder(
                "pandoc",
                "--from=" + fromFormat,
                "--to=" + toFormat,
                "--wrap=auto",
                "--columns=" + PANDOC_WRAP_COLUMNS);
        processBuilder.redirectErrorStream(true);

        Process process = processBuilder.start();

        // Write input to pandoc's stdin
        try (var outputStream = process.getOutputStream()) {
            outputStream.write(input.getBytes(StandardCharsets.UTF_8));
            outputStream.flush();
        }

        // Read output from pandoc's stdout
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }

        // Wait for process to complete
        boolean finished = process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new CodegenException("Pandoc process timed out after " + TIMEOUT_SECONDS + " seconds");
        }

        int exitCode = process.exitValue();
        if (exitCode != 0) {
            throw new CodegenException(
                    "Pandoc failed with exit code " + exitCode + ": " + output.toString().trim());
        }

        return output.toString();
    }

    /**
     * Post-processes pandoc output for Python docstrings.
     *
     * @param output The raw output from pandoc
     * @return Post-processed Markdown suitable for Python docstrings
     */
    private static String postProcessPandocOutput(String output) {
        // Remove empty lines at the start and end
        output = output.trim();

        // Remove unnecessary backslash escapes that pandoc adds for markdown
        // These characters don't need escaping in Python docstrings
        // Handles: [ ] ' { } ( ) < > ` @ _ * | ! ~ $
        output = output.replaceAll("\\\\([\\[\\]'{}()<>`@_*|!~$])", "$1");

        // Replace <note> and <important> tags with admonitions for mkdocstrings
        output = replaceAdmonitionTags(output, "note", "Note");
        output = replaceAdmonitionTags(output, "important", "Warning");

        // Escape Smithy format specifiers
        return output.replace("$", "$$");
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
