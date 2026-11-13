/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;

public class MarkdownConverterTest {

    @Test
    public void testConvertHtmlToMarkdownWithTitleAndParagraph() {
        String html = "<h1>Title</h1><p>Paragraph</p>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should contain markdown heading and paragraph
        String expected = """
                # Title

                Paragraph""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithList() {
        String html = "<ul><li>Item 1</li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should contain markdown list
        String expected = """
                - Item 1
                - Item 2""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithBoldTag() {
        String html = "<b>Bold text</b>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("**Bold text**", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithItalicTag() {
        String html = "<i>Italic text</i>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("*Italic text*", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithCodeTag() {
        String html = "<code>code snippet</code>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("`code snippet`", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithAnchorTag() {
        String html = "<a href=\"https://example.com\">Link</a>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("[Link](https://example.com)", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithNestedList() {
        String html = "<ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
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
                MarkdownConverter.convert(html, createMockContext(true)));
        assertEquals("Testing $placeholderOne and $placeholderTwo",
                MarkdownConverter.convertForDocstring(html, createMockContext(true)));
    }

    @Test
    public void testConvertCommonmarkWithEmbeddedHtmlForNonAwsService() {
        // For non-AWS services, input is CommonMark which may include embedded HTML
        // This tests the important path where commonmark -> html -> markdown conversion happens
        String commonmarkWithHtml = "# Title\n\nParagraph with **bold** text and <em>embedded HTML</em>.";
        String result = MarkdownConverter.convert(commonmarkWithHtml, createMockContext(false));
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
        String result = MarkdownConverter.convert(commonmark, createMockContext(false));
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
        String result = MarkdownConverter.convert(html, createMockContext(true));
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
        assertEquals("`@[\\\\]^`", MarkdownConverter.convert(html, createMockContext(true)));
        assertEquals("`@[\\\\\\\\]^`", MarkdownConverter.convertForDocstring(html, createMockContext(true)));
    }

    @Test
    public void testConvertEscapesLoneBackslash() {
        // A lone backslash that is not part of a recognized Python escape (here a
        // backslash followed by a space) must be doubled so the docstring is a
        // valid Python string. Markdown has nothing to escape.
        String html = "<code>[ \\ ]</code>";
        assertEquals("`[ \\ ]`", MarkdownConverter.convert(html, createMockContext(true)));
        assertEquals("`[ \\\\ ]`", MarkdownConverter.convertForDocstring(html, createMockContext(true)));
    }

    @Test
    public void testConvertEscapesBackslashesThatLookLikePythonEscapes() {
        // A backslash of code that happens to form a valid Python escape (e.g. \")
        // is still a backslash. Left untouched, it would decode to something else.
        String html = "<code>!\\\"#</code>";
        assertEquals("`!\\\"#`", MarkdownConverter.convert(html, createMockContext(true)));
        assertEquals("`!\\\\\"#`", MarkdownConverter.convertForDocstring(html, createMockContext(true)));
    }

    @Test
    public void testConvertHandlesBackslashBeforeMarkdownChar() {
        // A backslash of code followed by a Markdown-significant character (here
        // "*") is not one of pandoc's escapes, so it is not dropped as they are.
        String html = "<code>arn:aws:iam::\\*:user/\\*</code>";
        assertEquals("`arn:aws:iam::\\*:user/\\*`", MarkdownConverter.convert(html, createMockContext(true)));
        assertEquals("`arn:aws:iam::\\\\*:user/\\\\*`",
                MarkdownConverter.convertForDocstring(html, createMockContext(true)));
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
                        MarkdownConverter.convert(prose, createMockContext(true)),
                        "Markdown without a code backslash"),
                () -> assertEquals("Glyph " + glyph + " is literal.",
                        MarkdownConverter.convertForDocstring(prose, createMockContext(true)),
                        "docstring without a code backslash"),
                () -> assertEquals("Glyph " + glyph + " is literal, as in `D:\\Users\\" + glyph + "`.",
                        MarkdownConverter.convert(withCode, createMockContext(true)),
                        "Markdown with code backslashes"),
                () -> assertEquals("Glyph " + glyph + " is literal, as in `D:\\\\Users\\\\" + glyph + "`.",
                        MarkdownConverter.convertForDocstring(withCode, createMockContext(true)),
                        "docstring with code backslashes"));
    }

    @Test
    public void testConvertHandlesBackslashStarNextToQuote() {
        // The API Gateway model documents the comment marker "\*/". Next to a quote,
        // pandoc emits an odd-length backslash run; the result must stay a valid
        // Python literal.
        String html = "<p>Do not include \"\\*/\" characters</p>";
        String result = MarkdownConverter.convert(html, createMockContext(true)).trim();
        assertEquals("Do not include \\\"\\\\*/\\\" characters", result);
    }

    @Test
    public void testConvertEscapesTripleQuotes() {
        // S3 documents QuoteEscapeCharacter with the example """ a , b """. Left
        // unescaped it would end the surrounding docstring early. Shorter quote
        // runs are left alone.
        String html = "<p>The value <code>\"\"\" a , b \"\"\"</code> is parsed as <code>\" a , b \"</code>.</p>";
        String result = MarkdownConverter.convertForDocstring(html, createMockContext(true)).trim();
        assertEquals("The value `\\\"\\\"\\\" a , b \\\"\\\"\\\"` is parsed as `\" a , b \"`.", result);
    }

    @Test
    public void testConvertEscapesQuoteRunsNextToBackslashes() {
        // The backslashes of code are literal, so they are doubled and never escape
        // the quote after them: every quote of each of these runs is escaped.
        String html = "<code>\"\"\"\"</code> <code>\\\"\"\"\"</code> <code>\\\\\"\"\"</code>";
        String result = MarkdownConverter.convertForDocstring(html, createMockContext(true)).trim();
        assertEquals("`\\\"\\\"\\\"\\\"` `\\\\\\\"\\\"\\\"\\\"` `\\\\\\\\\\\"\\\"\\\"`", result);
    }

    @Test
    public void testConvertEscapesTrailingQuote() {
        // A quote at the very end would run into the closing quotes of a
        // single-line docstring.
        String html = "<pre>x = \"a\"</pre>";
        String result = MarkdownConverter.convertForDocstring(html, createMockContext(true)).trim();
        assertEquals("x = \"a\\\"", result);
    }

    @Test
    public void testConvertMixedElements() {
        String html = "<h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = "# Title\n\nParagraph\n\n- Item 1\n- Item 2";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertNestedElements() {
        String html = "<h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
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
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = """
                This is a very long line that exceeds seventy-two characters and should
                wrap into two lines.""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithNoteTag() {
        String html = "<note>Note text</note>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should convert to admonition format
        String expected = """
                Note:
                    Note text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithImportantTag() {
        String html = "<important>Important text</important>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
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
        String result = MarkdownConverter.convert(html, createMockContext(true));

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
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = """
                Some text

                More text""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertBoldWithNestedFormatting() {
        String html = "<b><code>Test</code> test <a href=\"https://testing.com\">Link</a></b>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("**`Test` test [Link](https://testing.com)**", result);
    }

    @Test
    public void testConvertHrefWithSpaces() {
        String html = "<p><a href=\"  https://testing.com  \">Link</a></p>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Leading and trailing spaces must be trimmed
        assertEquals("[Link](https://testing.com)", result);
    }

    @Test
    public void testConvertLinkWithNestedCode() {
        String html = "<a href=\"https://testing.com\"><code>Link</code></a>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("[`Link`](https://testing.com)", result);
    }

    @Test
    public void testConvertCodeWithNestedLinkSpaces() {
        String html = "<code> <a href=\"https://testing.com\">Link</a> </code>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("` `[`Link`](https://testing.com)` `", result);
    }

    @Test
    public void testConvertCodeWithNestedLinkNoSpaces() {
        String html = "<code><a href=\"https://testing.com\">Link</a></code>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("[`Link`](https://testing.com)", result);
    }

    @Test
    public void testConvertCodeWithNestedEmptyLink() {
        String html = "<code><a>Link</a></code>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
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

    private GenerationContext createMockContext(boolean isAwsService) {
        GenerationContext context = mock(GenerationContext.class);
        Model model = mock(Model.class);
        PythonSettings settings = mock(PythonSettings.class);

        ShapeId serviceId = ShapeId.from("test.service#TestService");
        ServiceShape serviceShape = mock(ServiceShape.class);

        when(context.model()).thenReturn(model);
        when(context.settings()).thenReturn(settings);
        when(settings.service()).thenReturn(serviceId);
        when(model.expectShape(serviceId)).thenReturn(serviceShape);

        if (isAwsService) {
            when(serviceShape.hasTrait(software.amazon.smithy.aws.traits.ServiceTrait.class)).thenReturn(true);
        } else {
            when(serviceShape.hasTrait(software.amazon.smithy.aws.traits.ServiceTrait.class)).thenReturn(false);
        }

        return context;
    }
}
