/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.python.codegen.writer.MarkdownToRstDocConverter;

public class MarkdownToRstDocConverterTest {

    private MarkdownToRstDocConverter markdownToRstDocConverter;

    @BeforeEach
    public void setUp() {
        markdownToRstDocConverter = MarkdownToRstDocConverter.getInstance();
    }

    @Test
    public void testConvertCommonmarkToRstWithTitleAndParagraph() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>";
        String expected = "Title\n=====\nParagraph";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithImportantNote() {
        String html = "<html><body><important>Important note</important></body></html>";
        String expected = ".. important::\n    Important note";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithList() {
        String html = "<html><body><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String expected = "* Item 1\n* Item 2";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithMixedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String expected = "Title\n=====\nParagraph\n\n\n* Item 1\n* Item 2";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithNestedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p></body></html>";
        String expected = "Title\n=====\nParagraph with **bold** text";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithAnchorTag() {
        String html = "<html><body><a href='https://example.com'>Link</a></body></html>";
        String expected = "`Link <https://example.com>`_";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithBoldTag() {
        String html = "<html><body><b>Bold text</b></body></html>";
        String expected = "**Bold text**";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithItalicTag() {
        String html = "<html><body><i>Italic text</i></body></html>";
        String expected = "*Italic text*";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithCodeTag() {
        String html = "<html><body><code>code snippet</code></body></html>";
        String expected = "``code snippet``";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithNoteTag() {
        String html = "<html><body><note>Note text</note></body></html>";
        String expected = ".. note::\n    Note text";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithNestedList() {
        String html = "<html><body><ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul></body></html>";
        String expected = "* Item 1\n\n    * Subitem 1\n* Item 2";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }

    @Test
    public void testConvertCommonmarkToRstWithFormatSpecifierCharacters() {
        // Test that Smithy format specifier characters ($) are properly escaped and treated as literal text
        String html = "<html><body><p>Testing $placeholder_one and $placeholder_two</p></body></html>";
        String expected = "Testing $placeholder_one and $placeholder_two";
        String result = markdownToRstDocConverter.convertCommonmarkToRst(html);
        assertEquals(expected, result.trim());
    }
}
