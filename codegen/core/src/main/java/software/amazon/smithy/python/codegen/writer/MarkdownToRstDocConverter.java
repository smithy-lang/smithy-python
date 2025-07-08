/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.jsoup.nodes.Document.OutputSettings.Syntax.html;

import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.commonmark.node.BlockQuote;
import org.commonmark.node.FencedCodeBlock;
import org.commonmark.node.Heading;
import org.commonmark.node.HtmlBlock;
import org.commonmark.node.ListBlock;
import org.commonmark.node.ThematicBreak;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Node;
import org.jsoup.nodes.TextNode;
import org.jsoup.select.NodeVisitor;
import software.amazon.smithy.utils.SetUtils;
import software.amazon.smithy.utils.SimpleCodeWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Add a runtime plugin to convert the HTML docs that are provided by services into RST
 */
@SmithyInternalApi
public class MarkdownToRstDocConverter {
    private static final Parser MARKDOWN_PARSER = Parser.builder()
            .enabledBlockTypes(SetUtils.of(
                    Heading.class,
                    HtmlBlock.class,
                    ThematicBreak.class,
                    FencedCodeBlock.class,
                    BlockQuote.class,
                    ListBlock.class))
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
        String html = HtmlRenderer.builder().escapeHtml(false).build().render(MARKDOWN_PARSER.parse(commonmark));
        //Replace the outer HTML paragraph tag with a div tag
        Pattern pattern = Pattern.compile("^<p>(.*)</p>$", Pattern.DOTALL);
        Matcher matcher = pattern.matcher(html);
        html = matcher.replaceAll("<div>$1</div>");
        Document document = Jsoup.parse(html);
        RstNodeVisitor visitor = new RstNodeVisitor();
        document.body().traverse(visitor);
        return "\n" + visitor;
    }

    private static class RstNodeVisitor implements NodeVisitor {
        SimpleCodeWriter writer = new SimpleCodeWriter();
        private boolean inList = false;
        private int listDepth = 0;

        @Override
        public void head(Node node, int depth) {
            if (node instanceof TextNode) {
                TextNode textNode = (TextNode) node;
                String text = textNode.text();
                if (!text.trim().isEmpty()) {
                    if (text.startsWith(":param ")) {
                        int secondColonIndex = text.indexOf(':', 1);
                        writer.write(text.substring(0, secondColonIndex + 1));
                        //TODO right now the code generator gives us a mixture of
                        // RST and HTML (for instance :param xyz: <p> docs
                        // </p>).  Since we standardize to html above, that <p> tag
                        // starts a newline.  We account for that with this if/else
                        // statement, but we should refactor this in the future to
                        // have a more elegant codepath.
                        if (secondColonIndex + 1 == text.strip().length()) {
                            writer.indent();
                            writer.ensureNewline();
                        } else {
                            writer.ensureNewline();
                            writer.indent();
                            writer.write(text.substring(secondColonIndex + 1));
                            writer.dedent();
                        }
                    } else {
                        writer.writeInline(text);
                    }
                    // Account for services making a paragraph tag that's empty except
                    // for a newline
                } else if (node.parent() != null && ((Element) node.parent()).tagName().equals("p")) {
                    writer.writeInline(text.replaceAll("[ \\t]+", ""));
                }
            } else if (node instanceof Element) {
                Element element = (Element) node;
                switch (element.tagName()) {
                    case "a":
                        writer.writeInline("`");
                        break;
                    case "b":
                    case "strong":
                        writer.writeInline("**");
                        break;
                    case "i":
                    case "em":
                        writer.writeInline("*");
                        break;
                    case "code":
                        writer.writeInline("``");
                        break;
                    case "important":
                        writer.ensureNewline();
                        writer.write("");
                        writer.openBlock(".. important::");
                        break;
                    case "note":
                        writer.ensureNewline();
                        writer.write("");
                        writer.openBlock(".. note::");
                        break;
                    case "ul":
                        if (inList) {
                            writer.indent();
                        }
                        inList = true;
                        listDepth++;
                        writer.ensureNewline();
                        writer.write("");
                        break;
                    case "li":
                        writer.writeInline("* ");
                        break;
                    case "h1":
                        writer.ensureNewline();
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
                        String href = element.attr("href");
                        if (!href.isEmpty()) {
                            writer.writeInline(" <").writeInline(href).writeInline(">`_");
                        } else {
                            writer.writeInline("`");
                        }
                        break;
                    case "b":
                    case "strong":
                        writer.writeInline("**");
                        break;
                    case "i":
                    case "em":
                        writer.writeInline("*");
                        break;
                    case "code":
                        writer.writeInline("``");
                        break;
                    case "important":
                    case "note":
                        writer.closeBlock("");
                        break;
                    case "p":
                        writer.ensureNewline();
                        writer.write("");
                        break;
                    case "ul":
                        listDepth--;
                        if (listDepth == 0) {
                            inList = false;
                        } else {
                            writer.dedent();
                        }
                        writer.ensureNewline();
                        break;
                    case "li":
                        writer.ensureNewline();
                        break;
                    case "h1":
                        String title = element.text();
                        writer.ensureNewline().writeInline("=".repeat(title.length())).ensureNewline();
                        break;
                    default:
                        break;
                }
            }
        }

        @Override
        public String toString() {
            return writer.toString();
        }
    }
}
