/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.utils.SmithyInternalApi;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.transform.ModelTransformer;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Node;
import org.jsoup.nodes.TextNode;
import org.jsoup.select.NodeVisitor;

/**
 * Add a runtime plugin to convert the HTML docs that are provided by services into
 * RST
 */
@SmithyInternalApi
public class AwsDocConverter implements PythonIntegration {
    @Override
    public Model preprocessModel(Model model, PythonSettings settings) {
        return ModelTransformer.create().mapShapes(model, shape -> {
            if (shape.hasTrait(DocumentationTrait.class)) {
                DocumentationTrait docTrait = shape.getTrait(DocumentationTrait.class).get();
                String html = docTrait.getValue();
                String rst = convertHtmlToRst(html);
                DocumentationTrait newDocTrait = new DocumentationTrait(rst);
                return Shape.shapeToBuilder(shape)
                        .addTrait(newDocTrait)
                        .build();
            } else {
                return shape;
            }
        });
    }

    private String convertHtmlToRst(String html) {
        Document document = Jsoup.parse(html);
        RstNodeVisitor visitor = new RstNodeVisitor();
        document.body().traverse(visitor);
        return "\n" + visitor;
    }

    private static class RstNodeVisitor implements NodeVisitor {
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
                }
            }
        }

        @Override
        public void tail(Node node, int depth) {
            if (node instanceof Element) {
                Element element = (Element) node;
                switch (element.tagName()) {
                    case "a":
                        sb.append(" <").append(element.attr("href")).append(">`_ ");
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
                    case "note", "p", "li":
                        sb.append("\n");
                        break;
                    case "ul":
                        listDepth--;
                        if (listDepth == 0) {
                            inList = false;
                        }
                        sb.append("\n\n");
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