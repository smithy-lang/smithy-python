/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

public class AwsDocConverterTest {

    private AwsDocConverter awsDocConverter;

    @BeforeEach
    public void setUp() {
        awsDocConverter = new AwsDocConverter();
    }

    @Test
    public void testConvertHtmlToRstWithTitleAndParagraph() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>";
        String expected = "\n\nTitle\n=====\nParagraph\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithImportantNote() {
        String html = "<html><body><important>Important note</important></body></html>";
        String expected = "\n\n.. important::\n    Important note\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithList() {
        String html = "<html><body><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String expected = "\n\n* Item 1\n\n* Item 2\n\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithMixedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";
        String expected = "\n\nTitle\n=====\nParagraph\n\n* Item 1\n\n* Item 2\n\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithNestedElements() {
        String html = "<html><body><h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p></body></html>";
        String expected = "\n\nTitle\n=====\nParagraph with **bold** text\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithAnchorTag() {
        String html = "<html><body><a href='https://example.com'>Link</a></body></html>";
        String expected = "\n`Link <https://example.com>`_";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithBoldTag() {
        String html = "<html><body><b>Bold text</b></body></html>";
        String expected = "\n**Bold text**";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithItalicTag() {
        String html = "<html><body><i>Italic text</i></body></html>";
        String expected = "\n*Italic text*";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithCodeTag() {
        String html = "<html><body><code>code snippet</code></body></html>";
        String expected = "\n``code snippet``";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithNoteTag() {
        String html = "<html><body><note>Note text</note></body></html>";
        String expected = "\n\n.. note::\n    Note text\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }

    @Test
    public void testConvertHtmlToRstWithNestedList() {
        String html = "<html><body><ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul></body></html>";
        String expected = "\n\n* Item 1\n  * Subitem 1\n\n* Item 2\n\n";
        String result = awsDocConverter.convertHtmlToRst(html);
        assertEquals(expected, result);
    }
}
