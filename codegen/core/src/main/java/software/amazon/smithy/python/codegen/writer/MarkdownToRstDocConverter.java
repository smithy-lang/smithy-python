/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Node;
import org.jsoup.nodes.TextNode;
import org.jsoup.select.NodeVisitor;
import software.amazon.smithy.utils.SetUtils;
import software.amazon.smithy.utils.SmithyInternalApi;
import org.commonmark.node.BlockQuote;
import org.commonmark.node.FencedCodeBlock;
import org.commonmark.node.Heading;
import org.commonmark.node.HtmlBlock;
import org.commonmark.node.ListBlock;
import org.commonmark.node.ThematicBreak;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;

import static org.jsoup.nodes.Document.OutputSettings.Syntax.html;

/**
 * Add a runtime plugin to convert the HTML docs that are provided by services into RST
 */
@SmithyInternalApi
public class MarkdownToRstDocConverter {
    private static final Parser MARKDOWN_PARSER = Parser.builder()
            .enabledBlockTypes(SetUtils.of(
                    Heading.class, HtmlBlock.class, ThematicBreak.class, FencedCodeBlock.class,
                    BlockQuote.class, ListBlock.class))
            .build();

    // Singleton instance
    private static final MarkdownToRstDocConverter DOC_CONVERTER = new MarkdownToRstDocConverter();

    // Private constructor to prevent instantiation
    private MarkdownToRstDocConverter() {
        // Constructor
    }

    public static MarkdownToRstDocConverter getInstance() {
        return DOC_CONVERTER;
    }


    public String convertCommonmarkToRst(String commonmark) {
        String html =
                HtmlRenderer.builder().escapeHtml(false).build().render(MARKDOWN_PARSER.parse(commonmark));
        Document document = Jsoup.parse(commonmark);
        RstNodeVisitor visitor = new RstNodeVisitor();
        document.body().traverse(visitor);
        return "\n" + visitor;
    }

    private static class RstNodeVisitor implements NodeVisitor {
        //TODO migrate away from StringBuilder to use a SimpleCodeWriter
        private final StringBuilder sb = new StringBuilder();
        private boolean inList = false;
        private int listDepth = 0;

        @Override
        public void head(Node node, int depth) {
            if (node instanceof TextNode) {
                TextNode textNode = (TextNode) node;
                String text = textNode.text();
                if (!text.trim().isEmpty()) {
                    sb.append(text);
                    // Account for services making a paragraph tag that's empty except
                    // for a newline
                } else if (node.parent() instanceof Element && ((Element) node.parent()).tagName().equals("p")) {
                    sb.append(text.replaceAll("[ \\t]+", ""));
                }
            } else if (node instanceof Element) {
                Element element = (Element) node;
                switch (element.tagName()) {
                    case "a":
                        sb.append("`");
                        break;
                    case "b":
                    case "strong":
                        sb.append("**");
                        break;
                    case "i":
                    case "em":
                        sb.append("*");
                        break;
                    case "code":
                        sb.append("``");
                        break;
                    case "important":
                        sb.append("\n.. important::\n    ");
                        break;
                    case "note":
                        sb.append("\n.. note::\n    ");
                        break;
                    case "ul":
                        inList = true;
                        listDepth++;
                        sb.append("\n");
                        break;
                    case "li":
                        if (inList) {
                            sb.append("  ".repeat(listDepth - 1)).append("* ");
                        }
                        break;
                    case "h1":
                        sb.append("\n");
                        break;
                    default:
                        break;
                }
            }
        }

        @Override
        public void tail(Node node, int depth) {
            if (node instanceof Element) {
                Element element = (Element) node;
                switch (element.tagName()) {
                    case "a":
                        sb.append(" <").append(element.attr("href")).append(">`_");
                        break;
                    case "b":
                    case "strong":
                        sb.append("**");
                        break;
                    case "i":
                    case "em":
                        sb.append("*");
                        break;
                    case "code":
                        sb.append("``");
                        break;
                    case "important":
                    case "note":
                    case "p":
                        sb.append("\n");
                        break;
                    case "ul":
                        listDepth--;
                        if (listDepth == 0) {
                            inList = false;
                        }
                        if (sb.charAt(sb.length() - 1) != '\n') {
                            sb.append("\n\n");
                        }
                        break;
                    case "li":
                        if (sb.charAt(sb.length() - 1) != '\n') {
                            sb.append("\n\n");
                        }
                        break;
                    case "h1":
                        String title = element.text();
                        sb.append("\n").append("=".repeat(title.length())).append("\n");
                        break;
                    default:
                        break;
                }
            }
        }

        @Override
        public String toString() {
            return sb.toString();
        }
    }
}