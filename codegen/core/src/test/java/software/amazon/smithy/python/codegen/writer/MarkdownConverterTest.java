/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeFalse;
import static org.junit.jupiter.api.Assumptions.assumeTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;

public class MarkdownConverterTest {

    private static final String BYTE_ORDER_MARK = String.valueOf((char) 0xFEFF);
    private static final boolean IS_WINDOWS = System.getProperty("os.name", "").startsWith("Windows");
    private static final boolean WORKER_SUPPORTED = !IS_WINDOWS && pandocLuaReportsVersion32OrLater();

    private final List<GenerationContext> contexts = new ArrayList<>();

    @Test
    public void testConvertHtmlToMarkdownWithTitleAndParagraph() {
        String html = "<h1>Title</h1><p>Paragraph</p>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should contain markdown heading and paragraph
        String expected = """
                # Title

                Paragraph""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithList() {
        String html = "<ul><li>Item 1</li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should contain markdown list
        String expected = """
                - Item 1
                - Item 2""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithBoldTag() {
        String html = "<b>Bold text</b>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("**Bold text**", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithItalicTag() {
        String html = "<i>Italic text</i>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("*Italic text*", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithCodeTag() {
        String html = "<code>code snippet</code>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("`code snippet`", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithAnchorTag() {
        String html = "<a href=\"https://example.com\">Link</a>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("[Link](https://example.com)", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithNestedList() {
        String html = "<ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should contain nested markdown list with proper indentation
        String expected = """
                - Item 1
                  - Subitem 1
                - Item 2""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithFormatSpecifierCharacters() {
        // Smithy format specifier characters ($) are left as they are. Converted
        // documentation is literal text that writers pass with $L, so escaping it
        // here would double the dollar signs of anything not used as a format string.
        String html = "<p>Testing $placeholderOne and $placeholderTwo</p>";
        assertEquals("Testing $placeholderOne and $placeholderTwo",
                MarkdownConverter.convert(html, createContext(true)));
        assertEquals("Testing $placeholderOne and $placeholderTwo",
                MarkdownConverter.convertForDocstring(html, createContext(true)));
    }

    @Test
    public void testConvertCommonmarkWithEmbeddedHtmlForNonAwsService() {
        // For non-AWS services, input is CommonMark which may include embedded HTML
        // This tests the important path where commonmark -> html -> markdown conversion happens
        String commonmarkWithHtml = "# Title\n\nParagraph with **bold** text and <em>embedded HTML</em>.";
        String result = MarkdownConverter.convert(commonmarkWithHtml, createContext(false));
        // Should properly handle both markdown syntax and embedded HTML
        String expected = """
                # Title

                Paragraph with **bold** text and *embedded HTML*.""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertPureCommonmarkForNonAwsService() {
        // For non-AWS services with pure CommonMark (no embedded HTML)
        String commonmark = "# Title\n\nParagraph with **bold** and *italic* text.\n\n- List item 1\n- List item 2";
        String result = MarkdownConverter.convert(commonmark, createContext(false));
        // Should preserve the markdown structure (pandoc uses single space after dash)
        String expected = """
                # Title

                Paragraph with **bold** and *italic* text.

                - List item 1
                - List item 2""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertRemovesUnnecessaryBackslashEscapes() {
        // Pandoc adds escapes for these characters but they're not needed in Python docstrings
        String html = "<p>Text with [brackets] and {braces} and (parens)</p>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should not have backslash escapes for these characters
        assertEquals("Text with [brackets] and {braces} and (parens)", result.trim());
    }

    // Code is verbatim in Markdown, so the four tests below expect every backslash
    // of the model in the plain Markdown, and twice in a docstring, where it then
    // decodes to itself whatever follows it.

    @Test
    public void testConvertPreservesLiteralDoubleBackslash() {
        // A literal "\\" (e.g. a password charset like "[\\]") is two backslashes.
        String html = "<code>@[\\\\]^</code>";
        assertEquals("`@[\\\\]^`", MarkdownConverter.convert(html, createContext(true)));
        assertEquals("`@[\\\\\\\\]^`", MarkdownConverter.convertForDocstring(html, createContext(true)));
    }

    @Test
    public void testConvertEscapesLoneBackslash() {
        // A lone backslash that is not part of a recognized Python escape (here a
        // backslash followed by a space) must be doubled so the docstring is a
        // valid Python string. Markdown has nothing to escape.
        String html = "<code>[ \\ ]</code>";
        assertEquals("`[ \\ ]`", MarkdownConverter.convert(html, createContext(true)));
        assertEquals("`[ \\\\ ]`", MarkdownConverter.convertForDocstring(html, createContext(true)));
    }

    @Test
    public void testConvertEscapesBackslashesThatLookLikePythonEscapes() {
        // A backslash of code that happens to form a valid Python escape (e.g. \")
        // is still a backslash. Left untouched, it would decode to something else.
        String html = "<code>!\\\"#</code>";
        assertEquals("`!\\\"#`", MarkdownConverter.convert(html, createContext(true)));
        assertEquals("`!\\\\\"#`", MarkdownConverter.convertForDocstring(html, createContext(true)));
    }

    @Test
    public void testConvertHandlesBackslashBeforeMarkdownChar() {
        // A backslash of code followed by a Markdown-significant character (here
        // "*") is not one of pandoc's escapes, so it is not dropped as they are.
        String html = "<code>arn:aws:iam::\\*:user/\\*</code>";
        assertEquals("`arn:aws:iam::\\*:user/\\*`", MarkdownConverter.convert(html, createContext(true)));
        assertEquals("`arn:aws:iam::\\\\*:user/\\\\*`",
                MarkdownConverter.convertForDocstring(html, createContext(true)));
    }

    // U+E05C stands in for the backslashes of code while pandoc runs. Documentation
    // may contain that character itself, and there it is not a backslash.

    @Test
    public void testConvertKeepsLiteralPrivateUseCharacter() {
        assertPrivateUseCharacterIsKept(String.valueOf((char) 0xE05C));
    }

    @Test
    public void testConvertKeepsEntityEncodedPrivateUseCharacter() {
        // Pandoc decodes the entity, so the character first appears in its output.
        assertPrivateUseCharacterIsKept("&#xE05C;");
    }

    private void assertPrivateUseCharacterIsKept(String written) {
        String glyph = String.valueOf((char) 0xE05C);
        // Without a backslash of code nothing needs a stand-in. With one, the
        // character sits in prose and right after a backslash that does.
        String prose = "<p>Glyph " + written + " is literal.</p>";
        String withCode = "<p>Glyph " + written + " is literal, as in <code>D:\\Users\\" + written + "</code>.</p>";
        assertAll(
                () -> assertEquals("Glyph " + glyph + " is literal.",
                        MarkdownConverter.convert(prose, createContext(true)),
                        "Markdown without a code backslash"),
                () -> assertEquals("Glyph " + glyph + " is literal.",
                        MarkdownConverter.convertForDocstring(prose, createContext(true)),
                        "docstring without a code backslash"),
                () -> assertEquals("Glyph " + glyph + " is literal, as in `D:\\Users\\" + glyph + "`.",
                        MarkdownConverter.convert(withCode, createContext(true)),
                        "Markdown with code backslashes"),
                () -> assertEquals("Glyph " + glyph + " is literal, as in `D:\\\\Users\\\\" + glyph + "`.",
                        MarkdownConverter.convertForDocstring(withCode, createContext(true)),
                        "docstring with code backslashes"));
    }

    @Test
    public void testConvertHandlesBackslashStarNextToQuote() {
        // The API Gateway model documents the comment marker "\*/". Next to a quote,
        // pandoc emits an odd-length backslash run; the result must stay a valid
        // Python literal.
        String html = "<p>Do not include \"\\*/\" characters</p>";
        String result = MarkdownConverter.convert(html, createContext(true)).trim();
        assertEquals("Do not include \\\"\\\\*/\\\" characters", result);
    }

    @Test
    public void testConvertEscapesTripleQuotes() {
        // S3 documents QuoteEscapeCharacter with the example """ a , b """. Left
        // unescaped it would end the surrounding docstring early. Shorter quote
        // runs are left alone.
        String html = "<p>The value <code>\"\"\" a , b \"\"\"</code> is parsed as <code>\" a , b \"</code>.</p>";
        String result = MarkdownConverter.convertForDocstring(html, createContext(true)).trim();
        assertEquals("The value `\\\"\\\"\\\" a , b \\\"\\\"\\\"` is parsed as `\" a , b \"`.", result);
    }

    @Test
    public void testConvertEscapesQuoteRunsNextToBackslashes() {
        // The backslashes of code are literal, so they are doubled and never escape
        // the quote after them: every quote of each of these runs is escaped.
        String html = "<code>\"\"\"\"</code> <code>\\\"\"\"\"</code> <code>\\\\\"\"\"</code>";
        String result = MarkdownConverter.convertForDocstring(html, createContext(true)).trim();
        assertEquals("`\\\"\\\"\\\"\\\"` `\\\\\\\"\\\"\\\"\\\"` `\\\\\\\\\\\"\\\"\\\"`", result);
    }

    @Test
    public void testConvertEscapesTrailingQuote() {
        // A quote at the very end would run into the closing quotes of a
        // single-line docstring. Pandoc leaves it verbatim in code, so only the
        // docstring conversion escapes it.
        String html = "<pre><code>end\"</code></pre>";
        GenerationContext context = createContext(true);
        assertEquals("end\"", MarkdownConverter.convert(html, context).trim());
        assertEquals("end\\\"", MarkdownConverter.convertForDocstring(html, context).trim());
    }

    @Test
    public void testConvertMixedElements() {
        String html = "<h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createContext(true));
        String expected = "# Title\n\nParagraph\n\n- Item 1\n- Item 2";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertNestedElements() {
        String html = "<h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p>";
        String result = MarkdownConverter.convert(html, createContext(true));
        String expected = """
                # Title

                Paragraph with **bold** text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertMultilineText() {
        // Create a string with content > 72 chars to trigger wrapping
        String html =
                "This is a very long line that exceeds seventy-two characters and should wrap into two lines.";
        String result = MarkdownConverter.convert(html, createContext(true));
        String expected = """
                This is a very long line that exceeds seventy-two characters and should
                wrap into two lines.""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithNoteTag() {
        String html = "<note>Note text</note>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should convert to admonition format
        String expected = """
                Note:
                    Note text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithImportantTag() {
        String html = "<important>Important text</important>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Should convert to warning admonition
        String expected = """
                Warning:
                    Important text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertMultilineAdmonitionTag() {
        // Create a note with content > 72 chars to trigger wrapping
        String longLine =
                "This is a very long line that exceeds seventy-two characters and should wrap into two lines.";
        String html = "<note>" + longLine + "</note>";
        String result = MarkdownConverter.convert(html, createContext(true));

        // Expected: first line up to 72 chars, rest on second line, both indented
        String expected = """
                Note:
                    This is a very long line that exceeds seventy-two characters and should
                    wrap into two lines.""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertExcludesFullnameTag() {
        String html = "<p>Some text</p><fullname>AWS Service Name</fullname><p>More text</p>";
        String result = MarkdownConverter.convert(html, createContext(true));
        String expected = """
                Some text

                More text""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertBoldWithNestedFormatting() {
        String html = "<b><code>Test</code> test <a href=\"https://testing.com\">Link</a></b>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("**`Test` test [Link](https://testing.com)**", result);
    }

    @Test
    public void testConvertHrefWithSpaces() {
        String html = "<p><a href=\"  https://testing.com  \">Link</a></p>";
        String result = MarkdownConverter.convert(html, createContext(true));
        // Leading and trailing spaces must be trimmed
        assertEquals("[Link](https://testing.com)", result);
    }

    @Test
    public void testConvertLinkWithNestedCode() {
        String html = "<a href=\"https://testing.com\"><code>Link</code></a>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("[`Link`](https://testing.com)", result);
    }

    @Test
    public void testConvertCodeWithNestedLinkSpaces() {
        String html = "<code> <a href=\"https://testing.com\">Link</a> </code>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("` `[`Link`](https://testing.com)` `", result);
    }

    @Test
    public void testConvertCodeWithNestedLinkNoSpaces() {
        String html = "<code><a href=\"https://testing.com\">Link</a></code>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("[`Link`](https://testing.com)", result);
    }

    @Test
    public void testConvertCodeWithNestedEmptyLink() {
        String html = "<code><a>Link</a></code>";
        String result = MarkdownConverter.convert(html, createContext(true));
        assertEquals("`Link`", result);
    }

    @Test
    public void testLeadParagraphEndsAtTheFirstBlankLine() {
        String wrapped = "The value can\nrange from 900 seconds.";
        assertEquals(wrapped.length(), MarkdownConverter.leadParagraphEnd(wrapped));
        assertEquals(wrapped.length(), MarkdownConverter.leadParagraphEnd(wrapped + "\n\n- A list.\n"));
        assertEquals(wrapped.length(), MarkdownConverter.leadParagraphEnd(wrapped + "\n\n    code\n"));
        // An autolink is text; other raw HTML may be a block.
        String link = "<https://example.com> describes\nthe value.";
        assertEquals(link.length(), MarkdownConverter.leadParagraphEnd(link));
    }

    @Test
    public void testLeadParagraphIsOnlyEverAParagraph() {
        // Joining the lines of any of these would change what they mean.
        for (String notAParagraph : new String[] {
                "",
                "- One.\n- Two.",
                "1. One.\n2. Two.",
                "    code\n    more code",
                "```python\ncode\n```",
                "# Heading",
                "Heading\n-------",
                "> A quote\n> continues.",
                "| a | b |\n|---|---|",
                "Term\n:   Definition",
                "Note:\n    An admonition.",
                "Text with a note. Note:\n    An admonition.",
                "<div>\nraw HTML\n</div>",
                "A hard line break\\\nends this line.",
        }) {
            assertEquals(-1, MarkdownConverter.leadParagraphEnd(notAParagraph), notAParagraph);
        }
        // A doubled backslash at the end of a line is a literal one, not a line break.
        String literal = "Ends with a backslash \\\\\nand goes on.";
        assertEquals(literal.length(), MarkdownConverter.leadParagraphEnd(literal));
    }

    @Test
    public void testDistinctConversionsInOneGenerationShareOnePandocProcess() throws IOException {
        // Pandoc startup dominates generation time, so converting different
        // documentation strings within one generation must not launch a Pandoc
        // process per string.
        GenerationContext context = createContext(true);
        long pandocStarts = countPandocStartsOnCurrentThread(() -> {
            assertEquals("**Bold text**", MarkdownConverter.convert("<b>Bold text</b>", context));
            assertEquals("*Italic text*", MarkdownConverter.convert("<i>Italic text</i>", context));
            assertEquals("`code snippet`", MarkdownConverter.convert("<code>code snippet</code>", context));
        });
        if (WORKER_SUPPORTED) {
            assertEquals(1, pandocStarts, "Pandoc processes started for three distinct conversions");
        } else {
            // Windows and Pandoc before 3.2 start Pandoc per conversion, as before.
            assertFalse(context.pandocWorker().isRunning());
        }
    }

    @Test
    public void testWorkerMatchesCommandLineForAwsDocumentation() {
        assertWorkerMatchesCommandLine(createContext(true),
                List.of(
                        "<p>Use <code>$value</code>, a \\ backslash, [brackets] and "
                                + "<code>\"\"\"quotes\"\"\"</code>.</p>",
                        "<note>This is a very long line that exceeds seventy-two characters "
                                + "and should wrap into two lines.</note>",
                        "<pre>first line\r\n\tindented\tafter a tab</pre><p>a\r\nb</p>",
                        BYTE_ORDER_MARK + "<ul><li>Item<ul><li>Sub</li></ul></li></ul><important>Careful</important>",
                        "<p><a href=\" https://example.com \">link</a> <fullname>Name</fullname>and text</p>"));
    }

    @Test
    public void testWorkerMatchesCommandLineForGenericDocumentation() {
        assertWorkerMatchesCommandLine(createContext(false),
                List.of(
                        "# Title\n\nParagraph with **bold**, <em>embedded HTML</em> and a $dollar.\n",
                        "```python\nprint(\"hi\")\n```\n\n- item\n\n        indented code\twith a tab\n",
                        "Text with `code \\\\ backslash` and \"\"\"triple quotes\"\"\"\r\n"));
    }

    @Test
    public void testClosingOneGenerationLeavesAnotherRunning() {
        GenerationContext first = createContext(true);
        GenerationContext second = createContext(true);
        assertEquals("**a**", MarkdownConverter.convert("<b>a</b>", first));
        assertEquals("*b*", MarkdownConverter.convert("<i>b</i>", second));

        first.pandocWorker().close();

        assertFalse(first.pandocWorker().isRunning());
        assertEquals(WORKER_SUPPORTED, second.pandocWorker().isRunning());
        assertEquals("`c`", MarkdownConverter.convert("<code>c</code>", second));
        // A closed generation still converts, with the command line rather than a new worker.
        assertEquals("**a**", MarkdownConverter.convert("<b>a</b>", first));
        assertFalse(first.pandocWorker().isRunning());
    }

    @Test
    public void testPandocWithoutWorkerSupportFallsBackToCommandLine() throws Exception {
        // "pandoc --version" exits without the worker handshake, like Pandoc older than 3.2.
        try (PandocWorker worker = new PandocWorker(List.of("pandoc", "--version"), Duration.ofSeconds(10))) {
            assertTrue(worker.convert("<b>Bold text</b>", "html+raw_html", "markdown").isEmpty());
            assertEquals("**Bold text**", MarkdownConverter.convert("<b>Bold text</b>", createContext(true), worker));
            assertFalse(worker.isRunning());
        }
    }

    @Test
    public void testWorkerThatExitsFailsInsteadOfFallingBack() {
        assumeTrue(WORKER_SUPPORTED, "Windows or this pandoc cannot run a worker");
        try (PandocWorker worker = new PandocWorker(
                List.of("pandoc", "lua", "-e", "io.write('READY test\\n') io.flush()"),
                Duration.ofSeconds(10))) {
            GenerationContext context = createContext(true);
            assertThrows(CodegenException.class, () -> MarkdownConverter.convert("<b>a</b>", context, worker));
            // The failure is not forgotten: later conversions fail too.
            assertThrows(CodegenException.class, () -> MarkdownConverter.convert("<b>a</b>", context, worker));
        }
    }

    @Test
    public void testWorkerThatStopsReadingTimesOutAndStops() {
        assumeTrue(WORKER_SUPPORTED, "Windows or this pandoc cannot run a worker");
        // The worker never reads, so writing a large document blocks once the pipe is full.
        try (PandocWorker worker = new PandocWorker(
                List.of("pandoc", "lua", "-e", "io.write('READY test\\n') io.flush() while true do end"),
                Duration.ofSeconds(1))) {
            String input = "<p>" + "x".repeat(4 * 1024 * 1024) + "</p>";
            CodegenException e = assertThrows(CodegenException.class,
                    () -> MarkdownConverter.convert(input, createContext(true), worker));
            assertTrue(e.getMessage().contains("timed out"), e.getMessage());
            worker.close();
            assertFalse(worker.isRunning());
        }
    }

    @Test
    public void testCloseStopsWorkerWhileAConversionIsBlocked() throws Exception {
        assumeTrue(WORKER_SUPPORTED, "Windows or this pandoc cannot run a worker");
        // The worker never reads, so the conversion blocks writing once the pipe is full,
        // holding the pipe's lock. Its loop ends after 30 seconds in case it is not stopped.
        PandocWorker worker = new PandocWorker(
                List.of("pandoc",
                        "lua",
                        "-e",
                        "io.write('READY test\\n') io.flush() local t = os.time() + 30 while os.time() < t do end"),
                Duration.ofSeconds(60));
        try {
            String input = "<p>" + "x".repeat(4 * 1024 * 1024) + "</p>";
            FutureTask<Optional<String>> conversion =
                    new FutureTask<>(() -> worker.convert(input, "html+raw_html", "markdown"));
            Thread thread = new Thread(conversion, "blocked-pandoc-conversion");
            thread.setDaemon(true);
            thread.start();
            long startDeadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
            while (!worker.isRunning() && !conversion.isDone() && System.nanoTime() < startDeadline) {
                Thread.sleep(10);
            }
            // Let the worker answer the handshake and the conversion fill the pipe.
            Thread.sleep(1000);
            assertFalse(conversion.isDone());

            assertTimeoutPreemptively(Duration.ofSeconds(5), worker::close);

            assertFalse(worker.isRunning());
            try {
                // Only if close() won the race with startup does the conversion fall back.
                assertEquals(Optional.empty(), conversion.get(5, TimeUnit.SECONDS));
            } catch (ExecutionException e) {
                assertTrue(e.getCause() instanceof IOException, e.getCause().toString());
            }
        } finally {
            worker.close();
        }
    }

    @Test
    public void testCommandLineFallbackStopsHungPandocAtDeadline() throws Exception {
        assumeFalse(IS_WINDOWS, "Uses the POSIX sleep command");
        // "sleep" never reads stdin and keeps stdout open: a large input blocks writing,
        // a small one blocks reading.
        for (String input : List.of("x".repeat(4 * 1024 * 1024), "<p>text</p>")) {
            long start = System.nanoTime();
            CodegenException e = assertThrows(CodegenException.class,
                    () -> MarkdownConverter.convertWithPandocCli(
                            List.of("sleep", "30"),
                            input,
                            Duration.ofSeconds(1)));
            assertTrue(e.getMessage().contains("timed out"), e.getMessage());
            assertTrue(System.nanoTime() - start < TimeUnit.SECONDS.toNanos(5), "Not stopped at the deadline");
            assertSleepChildrenExit();
        }
    }

    @Test
    public void testInterruptedCommandLineFallbackStopsPandoc() throws Exception {
        assumeFalse(IS_WINDOWS, "Uses the POSIX sleep command");
        Thread.currentThread().interrupt();
        try {
            assertThrows(InterruptedException.class,
                    () -> MarkdownConverter.convertWithPandocCli(
                            List.of("sleep", "30"),
                            "<p>text</p>",
                            Duration.ofSeconds(10)));
        } finally {
            Thread.interrupted();
        }
        assertSleepChildrenExit();
    }

    // Fails if a "sleep" started by this JVM keeps running.
    private static void assertSleepChildrenExit() throws Exception {
        List<ProcessHandle> children = ProcessHandle.current()
                .children()
                .filter(child -> child.info().command().map(command -> command.endsWith("sleep")).orElse(false))
                .toList();
        for (ProcessHandle child : children) {
            child.onExit().get(5, TimeUnit.SECONDS);
        }
    }

    // Decides, without PandocWorker, whether production should run a worker here: Pandoc's
    // lua command must exist and report Pandoc 3.2 or later. A broken worker on such a
    // Pandoc then fails the worker tests instead of skipping them.
    private static boolean pandocLuaReportsVersion32OrLater() {
        try {
            Process process = new ProcessBuilder(
                    "pandoc",
                    "lua",
                    "-e",
                    "local v = PANDOC_VERSION io.write((v[1] > 3 or v[1] == 3 and v[2] >= 2) and 'yes' or 'no')")
                    .redirectErrorStream(true)
                    .start();
            process.getOutputStream().close();
            if (!process.waitFor(30, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                return false;
            }
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            return process.exitValue() == 0 && output.equals("yes");
        } catch (IOException e) {
            return false;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    private static void assertWorkerMatchesCommandLine(GenerationContext context, List<String> inputs) {
        for (String input : inputs) {
            String commandLine = MarkdownConverter.convert(input, context, null);
            assertEquals(commandLine, MarkdownConverter.convert(input, context, context.pandocWorker()), input);
        }
        // Windows and Pandoc before 3.2 convert with the command line instead.
        assertEquals(WORKER_SUPPORTED, context.pandocWorker().isRunning());
    }

    private static long countPandocStartsOnCurrentThread(Runnable action) throws IOException {
        Path dump = Files.createTempFile("pandoc-starts", ".jfr");
        try (Recording recording = new Recording()) {
            recording.enable("jdk.ProcessStart").withoutStackTrace();
            recording.start();
            action.run();
            recording.stop();
            recording.dump(dump);
            long threadId = Thread.currentThread().getId();
            return RecordingFile.readAllEvents(dump)
                    .stream()
                    .filter(event -> event.getThread() != null && event.getThread().getJavaThreadId() == threadId)
                    .filter(MarkdownConverterTest::isPandocStart)
                    .count();
        } finally {
            Files.deleteIfExists(dump);
        }
    }

    private static boolean isPandocStart(RecordedEvent event) {
        String command = event.getString("command");
        if (command == null) {
            return false;
        }
        String program = command.split(" ", 2)[0].toLowerCase(Locale.ROOT);
        return program.endsWith("pandoc") || program.endsWith("pandoc.exe");
    }

    @AfterEach
    public void closeContexts() {
        contexts.forEach(context -> context.pandocWorker().close());
    }

    // A real GenerationContext, so its Pandoc worker is exercised. Closed after each test.
    private GenerationContext createContext(boolean isAwsService) {
        Model model = mock(Model.class);
        PythonSettings settings = mock(PythonSettings.class);
        ShapeId serviceId = ShapeId.from("test.service#TestService");
        ServiceShape serviceShape = mock(ServiceShape.class);

        when(settings.service()).thenReturn(serviceId);
        when(model.expectShape(serviceId)).thenReturn(serviceShape);
        when(serviceShape.hasTrait(ServiceTrait.class)).thenReturn(isAwsService);

        GenerationContext context = GenerationContext.builder().model(model).settings(settings).build();
        contexts.add(context);
        return context;
    }
}
