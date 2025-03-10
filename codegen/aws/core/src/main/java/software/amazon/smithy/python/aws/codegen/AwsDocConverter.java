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
 * Adds a runtime plugin to set user agent.
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
        return visitor.toString();
    }

    private static class RstNodeVisitor implements NodeVisitor {
        private final StringBuilder sb = new StringBuilder();
        private boolean inList = false;

        @Override
        public void head(Node node, int depth) {
            if (node instanceof TextNode) {
                //TODO properly handle stripping whitespace
                Node parentNode = node.parent();
                if (parentNode != null && parentNode.nodeName().equals("p")) {
                    //TODO write a test case like the following: <p> Foo <i>bar
                    // </i> baz</p> -> "Foo *bar* baz"
                    sb.append(((TextNode) node).text().strip());
                } else {
                    sb.append(((TextNode) node).text());
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
                        sb.append(" ``");
                        break;
                    case "important":
                        sb.append(".. important::\n\n    ");
                        break;
                    case "note":
                        sb.append(".. note::\n\n    ");
                        break;
                    //TODO this looks a little weird on modelid for invoke_model input
                    // do I do something weird based on if it's in a parameter cause
                    // those are already bullets?
                    case "ul":
                        inList = true;
                        sb.append("\n");
                        break;
                    case "li":
                        if (inList) {
                            sb.append("- ");
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
                        sb.append("`` ");
                        break;
                    case "important":
                    case "note":
                        sb.append("\n\n");
                        break;
                    case "ul":
                        inList = false;
                        sb.append("\n");
                        break;
                    case "p":
                        sb.append("\n\n");
                        break;
                }
            }
        }

        @Override
        public String toString() {
            return sb.toString().trim();
        }
    }
}