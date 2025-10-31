/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

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

    @Test
    public void testConvertHtmlToMarkdownWithTitleAndParagraph() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should contain markdown heading and paragraph
        String expected = """
                # Title

                Paragraph""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithList() {
        String html = "<html><body><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should contain markdown list
        String expected = """
                - Item 1
                - Item 2""";
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithBoldTag() {
        String html = "<html><body><b>Bold text</b></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("**Bold text**", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithItalicTag() {
        String html = "<html><body><i>Italic text</i></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("*Italic text*", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithCodeTag() {
        String html = "<html><body><code>code snippet</code></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("`code snippet`", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithAnchorTag() {
        String html = "<html><body><a href='https://example.com'>Link</a></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        assertEquals("[Link](https://example.com)", result);
    }

    @Test
    public void testConvertHtmlToMarkdownWithNestedList() {
        String html = "<html><body><ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul></body></html>";
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
        // Test that Smithy format specifier characters ($) are properly escaped
        String html = "<html><body><p>Testing $placeholderOne and $placeholderTwo</p></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // $ should be escaped to $$
        assertEquals("Testing $$placeholderOne and $$placeholderTwo", result);
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
        String html = "<html><body><p>Text with [brackets] and {braces} and (parens)</p></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should not have backslash escapes for these characters
        assertEquals("Text with [brackets] and {braces} and (parens)", result.trim());
    }

    @Test
    public void testConvertMixedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = "# Title\n\nParagraph\n\n- Item 1\n- Item 2";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertNestedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = """
                # Title

                Paragraph with **bold** text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertMultilineText() {
        // Create a note with content > 72 chars to trigger wrapping
        String longLine =
                "This is a very long line that exceeds seventy-two characters and should wrap into two lines.";
        String html = "<html><body>" + longLine + "</body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        String expected = """
                This is a very long line that exceeds seventy-two characters and should
                wrap into two lines.""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithNoteTag() {
        String html = "<html><body><note>Note text</note></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));
        // Should convert to admonition format
        String expected = """
                Note:
                    Note text""";
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertHtmlToMarkdownWithImportantTag() {
        String html = "<html><body><important>Important text</important></body></html>";
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
        String html = "<html><body><note>" + longLine + "</note></body></html>";
        String result = MarkdownConverter.convert(html, createMockContext(true));

        // Expected: first line up to 72 chars, rest on second line, both indented
        String expected = """
                Note:
                    This is a very long line that exceeds seventy-two characters and should
                    wrap into two lines.""";
        assertEquals(expected, result.trim());
    }
}
