/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.math.BigDecimal;
import java.util.Optional;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.BooleanNode;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.node.NodeVisitor;
import software.amazon.smithy.model.node.NullNode;
import software.amazon.smithy.model.node.NumberNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.CollectionShape;
import software.amazon.smithy.model.shapes.DocumentShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.HttpPayloadTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/**
 * NodeVisitor implementation for converting node values for
 * input shape(s) to proper Python values in the generated code.
 */
final class ValueNodeVisitor implements NodeVisitor<Void> {
    private final GenerationContext context;
    private final Model model;
    private final PythonWriter writer;
    private final Shape inputShape;

    /**
     * @param context The generation context.
     * @param writer The writer to write the value with.
     * @param inputShape The shape of the value.
     */
    ValueNodeVisitor(GenerationContext context, PythonWriter writer, Shape inputShape) {
        this.context = context;
        this.model = context.model();
        this.writer = writer;
        this.inputShape = inputShape;
    }

    /**
     * Writes the members of an operation's input as the keyword arguments of a call
     * to its client method, one per line. Nested values are written as models.
     *
     * @param node The value of the input structure this visitor was created for.
     */
    void writeKeywordArguments(ObjectNode node) {
        structureMemberShapes((StructureShape) inputShape, node, "$L = ");
    }

    /**
     * Writes the members of an operation's input as a dictionary of the keyword
     * arguments of a call to its client method, keyed by parameter name. Nested values
     * are written as models.
     *
     * @param node The value of the input structure this visitor was created for.
     */
    void writeKeywordDictionary(ObjectNode node) {
        writer.openBlock("{", "}", () -> structureMemberShapes((StructureShape) inputShape, node, "$S: "));
    }

    @Override
    public Void arrayNode(ArrayNode node) {
        var openList = "[";
        var closeList = "]";

        if (inputShape.isListShape()) {
            var target = model.expectShape(inputShape.asListShape().get().getMember().getTarget());
            if (target.isDocumentShape()) {
                var docName = writer.format("$T", RuntimeTypes.DOCUMENT);
                openList = docName + "([";
                closeList = "])";
            }
        }

        writer.openBlock(openList, closeList, () -> {
            // The target visitor won't change if the input shape is a union
            ValueNodeVisitor targetVisitor;
            if (inputShape instanceof CollectionShape) {
                var target = model.expectShape(((CollectionShape) inputShape).getMember().getTarget());
                targetVisitor = new ValueNodeVisitor(context, writer, target);
            } else {
                targetVisitor = this;
            }

            node.getElements().forEach(elementNode -> {
                writer.write("$C, ", (Runnable) () -> elementNode.accept(targetVisitor));
            });
        });
        return null;
    }

    @Override
    public Void booleanNode(BooleanNode node) {
        writer.writeInline(node.getValue() ? "True" : "False");
        return null;
    }

    @Override
    public Void nullNode(NullNode node) {
        writer.writeInline("None");
        return null;
    }

    @Override
    public Void numberNode(NumberNode node) {
        if (inputShape.isTimestampShape()) {
            var parsed = CodegenUtils.parseTimestampNode(model, inputShape, node);
            writer.writeInline(CodegenUtils.getDatetimeConstructor(writer, parsed));
        } else if (inputShape.isFloatShape() || inputShape.isDoubleShape()) {
            writer.writeInline("float($L)", node.getValue());
        } else if (inputShape.isBigDecimalShape()) {
            // A float literal would lose precision past ~17 digits and produce the
            // wrong type, so build the Decimal from the exact model text.
            writer.addStdlibImport("decimal", "Decimal");
            var value = node.getValue();
            var text = value instanceof BigDecimal bd ? bd.toPlainString() : value.toString();
            writer.writeInline("Decimal($S)", text);
        } else {
            writer.writeInline("$L", node.getValue());
        }
        return null;
    }

    @Override
    public Void objectNode(ObjectNode node) {
        switch (inputShape.getType()) {
            case STRUCTURE -> structureShape((StructureShape) inputShape, node);
            case MAP -> mapShape((MapShape) inputShape, node);
            case UNION -> unionShape((UnionShape) inputShape, node);
            case DOCUMENT -> documentShape((DocumentShape) inputShape, node);
            default -> throw new CodegenException("unexpected input shape: " + inputShape.getType());
        }
        return null;
    }

    @Override
    public Void stringNode(StringNode node) {
        if (inputShape.isBlobShape()) {
            writer.writeInline("b$S", node.getValue());
        } else if (inputShape.isFloatShape() || inputShape.isDoubleShape()) {
            var value = switch (node.getValue()) {
                case "NaN" -> "nan";
                case "Infinity" -> "inf";
                case "-Infinity" -> "-inf";
                default -> throw new CodegenException("Invalid value: " + node.getValue());
            };

            writer.writeInline("float($S)", value);
        } else {
            writer.writeInline("$S", node.getValue());
        }
        return null;
    }

    private Void structureShape(StructureShape shape, ObjectNode node) {
        writer.openBlock("$T(",
                ")",
                context.symbolProvider().toSymbol(shape),
                () -> structureMemberShapes(shape, node, "$L = "));
        return null;
    }

    // Writes one line per member that has a value. The key format takes the member's name.
    private Void structureMemberShapes(StructureShape container, ObjectNode node, String keyFormat) {
        for (MemberShape member : container.members()) {
            var optionalValueNode = node.getMember(member.getMemberName());
            if (optionalValueNode.isEmpty()) {
                if (isStringLikeOutputPayload(container, member)) {
                    // Massage these outputs to always be present because it will generally be impossible to
                    // determine the difference between an empty body and a missing body.
                    optionalValueNode = Optional.of(Node.from(""));
                } else {
                    continue;
                }
            }
            var valueNode = optionalValueNode.get();

            var targetShape = model.expectShape(member.getTarget());

            var formatString = keyFormat + "$C,";
            if (targetShape.isDocumentShape()) {
                var docName = writer.format("$T", RuntimeTypes.DOCUMENT);
                formatString = keyFormat + docName + "($C),";
            }

            writer.write(formatString,
                    context.symbolProvider().toMemberName(member),
                    (Runnable) () -> valueNode.accept(new ValueNodeVisitor(context, writer, targetShape)));

        }
        return null;
    }

    private boolean isStringLikeOutputPayload(StructureShape container, MemberShape member) {
        if (container.hasTrait(OutputTrait.class) && member.hasTrait(HttpPayloadTrait.class)) {
            var target = model.expectShape(member.getTarget());
            return target.isBlobShape() || target.isStringShape();
        }
        return false;
    }

    private Void mapShape(MapShape shape, ObjectNode node) {
        writer.openBlock("{",
                "}",
                () -> node.getMembers().forEach((keyNode, valueNode) -> {
                    var targetShape = model.expectShape(shape.getValue().getTarget());

                    var formatString = "$S: $C,";
                    if (targetShape.isDocumentShape()) {
                        var docName = writer.format("$T", RuntimeTypes.DOCUMENT);
                        formatString = "$S: " + docName + "($C),";
                    }

                    writer.write(formatString,
                            keyNode.getValue(),
                            (Runnable) () -> valueNode.accept(new ValueNodeVisitor(context, writer, targetShape)));
                }));
        return null;
    }

    private Void documentShape(DocumentShape shape, ObjectNode node) {
        writer.openBlock("{",
                "}",
                () -> node.getMembers().forEach((keyNode, valueNode) -> {
                    writer.write("$S: $C,",
                            keyNode.getValue(),
                            (Runnable) () -> valueNode.accept(this));
                }));
        return null;
    }

    private Void unionShape(UnionShape shape, ObjectNode node) {
        if (node.getMembers().size() == 1) {
            node.getMembers().forEach((keyNode, valueNode) -> {
                var memberShape = shape.getMember(keyNode.getValue())
                        .orElseThrow(() -> new CodegenException("unknown member: " + keyNode.getValue()));
                var targetShape = model.expectShape(memberShape.getTarget());
                unionShape(memberShape, targetShape, valueNode);
            });
        } else {
            throw new CodegenException("exactly 1 named member must be set.");
        }
        return null;
    }

    private Void unionShape(MemberShape memberShape, Shape targetShape, Node node) {
        writer.openBlock("$T(",
                ")",
                context.symbolProvider().toSymbol(memberShape),
                () -> writer.write("value = $C",
                        (Runnable) () -> node.accept(new ValueNodeVisitor(context, writer, targetShape))));
        return null;
    }
}
