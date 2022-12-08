/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import java.util.List;
import java.util.Optional;
import java.util.TreeSet;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
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
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.protocoltests.traits.AppliesTo;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestsTrait;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestCase;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestsTrait;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.Pair;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Generates protocol tests for a given HTTP protocol.
 *
 * <p>This should preferably be instantiated and used within an
 * implementation of a `ProtocolGeneration`
 */
@SmithyUnstableApi
public final class HttpProtocolTestGenerator implements Runnable {

    private static final Logger LOGGER = Logger.getLogger(HttpProtocolTestGenerator.class.getName());

    private final PythonSettings settings;
    private final Model model;
    private final ShapeId protocol;
    private final ServiceShape service;
    private final PythonWriter writer;
    private final GenerationContext context;

    public HttpProtocolTestGenerator(
            GenerationContext context,
            ShapeId protocol,
            PythonWriter writer
    ) {
        this.settings = context.settings();
        this.model = context.model();
        this.protocol = protocol;
        this.service = settings.getService(model);
        this.writer = writer;
        this.context = context;
    }

    /**
     * Generates the HTTP-based protocol tests for the given protocol in the model.
     */
    @Override
    public void run() {
        OperationIndex operationIndex = OperationIndex.of(model);
        TopDownIndex topDownIndex = TopDownIndex.of(model);

        // Use a TreeSet to have a fixed ordering of tests.
        for (OperationShape operation : new TreeSet<>(topDownIndex.getContainedOperations(service))) {

            // TODO: Add settings to configure which tests are generated (client or server)
            generateOperationTests(AppliesTo.CLIENT, operation, operationIndex);
        }
    }

    private void generateOperationTests(
            AppliesTo implementation,
            OperationShape operation,
            OperationIndex operationIndex) {

        // Request Tests
        operation.getTrait(HttpRequestTestsTrait.class).ifPresent(trait -> {
            for (HttpRequestTestCase testCase : trait.getTestCasesFor(implementation)) {
                onlyIfProtocolMatches(testCase, () -> generateRequestTest(operation, testCase));
            }
        });

        // Response Tests
        operation.getTrait(HttpResponseTestsTrait.class).ifPresent(trait -> {
            for (HttpResponseTestCase testCase : trait.getTestCasesFor(implementation)) {
                onlyIfProtocolMatches(testCase, () -> generateResponseTest(operation, testCase));
            }
        });

        // Error Tests
        for (StructureShape error : operationIndex.getErrors(operation, service)) {
            if (!error.hasTag("server-only")) {
                error.getTrait(HttpResponseTestsTrait.class).ifPresent(trait -> {
                    for (HttpResponseTestCase testCase : trait.getTestCasesFor(implementation)) {
                        onlyIfProtocolMatches(testCase,
                                () -> generateErrorResponseTest(operation, error, testCase));
                    }
                });
            }
        }
    }

    private void generateRequestTest(OperationShape operation, HttpRequestTestCase testCase) {
        // TODO: add logic for checking if should skip
        writeTestBlock(
                testCase,
                String.format("%s_request_%s", testCase.getId(), operation.getId().getName()),
                false,
                () -> {
            // TODO: Instantiate the client with the request interceptor
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.empty());

            // Generate the input using the expected shape and params
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);

            writer.write("input_ = $C\n",
                    (Runnable) () -> testCase.getParams().accept(new ValueNodeVisitor(inputShape))
            );

            writer.write("actual = await client.$T(input_)\n", context.symbolProvider().toSymbol(operation));

            // TODO: Correctly assert the response and other values
            writeAssertionBlock(testCase, List.of(Pair.of("actual", "actual")));
        });
    }

    private void generateResponseTest(OperationShape operation, HttpResponseTestCase testCase) {
        // TODO: Generate the real response test logic, add logic for skipping
        writeTestBlock(
                testCase,
                String.format("%s_response_%s", testCase.getId(), operation.getId().getName()),
                true,
                () -> {
            // TODO: Instantiate the client and interceptor
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.empty());

            // Create an empty input object to pass
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);
            writer.write("input_ = $C\n",
                    (Runnable) () -> (ObjectNode.builder().build()).accept(new ValueNodeVisitor(inputShape))
            );
            // Pass input to the operation and call it
            writer.write("actual = client.$T(input_)\n", context.symbolProvider().toSymbol(operation));

            // TODO: Correctly assert the response and other values
            writeAssertionBlock(testCase, List.of(Pair.of("actual", "actual")));
        });
    }

    private void generateErrorResponseTest(
            OperationShape operation,
            StructureShape error,
            HttpResponseTestCase testCase) {
        // TODO: Generate the real error response test logic, add logic for skipping
        writeTestBlock(testCase,
                String.format("%s_error_%s", testCase.getId(), operation.getId().getName()),
                false,
                () -> {
            // TODO: Instantiate the client and interceptor
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.empty());

            // Create an empty input object to pass
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);
            writer.write("input_ = $C\n",
                    (Runnable) () -> (Node.objectNode()).accept(new ValueNodeVisitor(inputShape))
            );
            // Pass input to the operation and call it
            writer.write("actual = client.$T(input_)\n", context.symbolProvider().toSymbol(operation));

            // TODO: Correctly assert the response and other values
            writeAssertionBlock(testCase, List.of(Pair.of("actual", "actual")));
        });
    }

    // Only generate test cases when protocol matches the target protocol.
    private <T extends HttpMessageTestCase> void onlyIfProtocolMatches(T testCase, Runnable runnable) {
        if (testCase.getProtocol().equals(protocol)) {
            LOGGER.fine(() -> String.format("Generating protocol test case for %s.%s",
                    service.getId(),
                    testCase.getId())
            );
            runnable.run();
        }
    }

    // write the test block, which may include certain decorators (i.e. `skip`)
    private void writeTestBlock(
            HttpMessageTestCase testCase,
            String testName,
            boolean shouldSkip,
            Runnable f
    ) {
        LOGGER.fine(String.format("Writing test block for %s", testName));
        writer.addDependency(SmithyPythonDependency.PYTEST);

        // Skipped tests are still generated, just not run.
        if (shouldSkip) {
            LOGGER.fine(String.format("Marking test (%s) as skipped.", testName));
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "mark", "mark");
            writer.write("@mark.skip()");
        }
        writer.openBlock("async def test_$L() -> None:", "", CaseUtils.toSnakeCase(testName), () -> {
            testCase.getDocumentation().ifPresent(writer::writeDocs);
            f.run();
        });
    }

    // write the client block, which may have additional configuration that should
    // be written when instantiating the client
    private void writeClientBlock(
            Symbol serviceSymbol,
            HttpMessageTestCase testCase,
            Optional<Runnable> additionalConfigurator
    ) {
        LOGGER.fine(String.format("Writing client block for %s in %s", serviceSymbol.getName(), testCase.getId()));

        writer.openBlock("client = $T(", ")\n", serviceSymbol, () -> {
            additionalConfigurator.ifPresent(Runnable::run);
        });
    }

    private void writeAssertionBlock(
            HttpMessageTestCase testCase,
            List<Pair<Object, Object>> assertions
    ) {
        LOGGER.fine(String.format("Writing assertions block for %s", testCase.getId()));

        assertions.forEach((assertion) -> {
            writer.write("assert $L == $L", assertion.left, assertion.right);
        });
    }

    /**
     * NodeVisitor implementation for converting node values for
     * input shape(s) to proper Python values in the generated code.
     */
    private final class ValueNodeVisitor implements NodeVisitor<Void> {
        private final Shape inputShape;

        private ValueNodeVisitor(Shape inputShape) {
            this.inputShape = inputShape;
        }

        @Override
        public Void arrayNode(ArrayNode node) {
            writer.openBlock("[", "]", () -> {
                // The target visitor won't change if the input shape is a union
                ValueNodeVisitor targetVisitor;
                if (inputShape instanceof CollectionShape) {
                    var target = model.expectShape(((CollectionShape) inputShape).getMember().getTarget());
                    targetVisitor = new ValueNodeVisitor(target);
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
            // TODO: Add support for timestamp, int-enum, and others
            if (inputShape.isTimestampShape()) {
                writer.addStdlibImport("datetime", "datetime");
                writer.writeInline("datetime.fromtimestamp($L)", node.getValue());
            } else if (inputShape.isFloatShape() || inputShape.isDoubleShape()) {
                writer.writeInline("float($L)", node.getValue());
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
            writer.openBlock("$T(", ")",
                    context.symbolProvider().toSymbol(shape),
                    () -> structureMemberShapes(shape, node)
            );
            return null;
        }

        private Void structureMemberShapes(StructureShape container, ObjectNode node) {
            node.getMembers().forEach((keyNode, valueNode) -> {
                var memberShape = container.getMember(keyNode.getValue()).orElseThrow(() ->
                        new CodegenException("unknown memberShape: " + keyNode.getValue())
                );
                var targetShape = model.expectShape(memberShape.getTarget());
                writer.write("$L = $C,",
                        context.symbolProvider().toMemberName(memberShape),
                        (Runnable) () -> valueNode.accept(new ValueNodeVisitor(targetShape))
                );
            });
            return null;
        }

        private Void mapShape(MapShape shape, ObjectNode node) {
            writer.openBlock("{", "}",
                    () -> node.getMembers().forEach((keyNode, valueNode) -> {
                        var targetShape = model.expectShape(shape.getValue().getTarget());
                        writer.write("$S: $C,",
                                keyNode.getValue(),
                                (Runnable) () -> valueNode.accept(new ValueNodeVisitor(targetShape))
                        );
                    })
            );
            return null;
        }

        private Void documentShape(DocumentShape shape, ObjectNode node) {
            writer.openBlock("{", "}",
                    () -> node.getMembers().forEach((keyNode, valueNode) -> {
                        writer.write("$S: $C,",
                                keyNode.getValue(),
                                (Runnable) () -> valueNode.accept(this)
                        );
                    })
            );
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
            writer.openBlock("$T(", ")",
                    context.symbolProvider().toSymbol(memberShape),
                    () -> writer.write("value = $C",
                            (Runnable) () -> node.accept(new ValueNodeVisitor(targetShape)))
            );
            return null;
        }
    }
}
