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

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.BiFunction;
import java.util.function.BiPredicate;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import java.util.stream.Stream;
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
    private static final Symbol REQUEST_TEST_ASYNC_HTTP_CLIENT_SYMBOL = Symbol.builder()
            .name("RequestTestAsyncHttpClient")
            .build();
    private static final Symbol RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL = Symbol.builder()
            .name("ResponseTestAsyncHttpClient")
            .build();
    private static final Symbol TEST_HTTP_SERVICE_ERR_SYMBOL = Symbol.builder()
            .name("TestHttpServiceError")
            .build();

    private final PythonSettings settings;
    private final Model model;
    private final ShapeId protocol;
    private final ServiceShape service;
    private final PythonWriter writer;
    private final GenerationContext context;
    private final BiPredicate<Shape, HttpMessageTestCase> testFilter;

    public HttpProtocolTestGenerator(
            GenerationContext context,
            ShapeId protocol,
            PythonWriter writer,
            BiPredicate<Shape, HttpMessageTestCase> testFilter
    ) {
        this.settings = context.settings();
        this.model = context.model();
        this.protocol = protocol;
        this.service = settings.getService(model);
        this.writer = writer;
        this.context = context;
        this.testFilter = testFilter;

        writer.putFormatter('J', new JavaToPythonFormatter());
    }

    public HttpProtocolTestGenerator(
        GenerationContext context,
        ShapeId protocol,
        PythonWriter writer
    ) {
        this(context, protocol, writer, (shape, testCase) -> false);
    }

    /**
     * Generates the HTTP-based protocol tests for the given protocol in the model.
     */
    @Override
    public void run() {
        OperationIndex operationIndex = OperationIndex.of(model);
        TopDownIndex topDownIndex = TopDownIndex.of(model);
        writer.addDependency(SmithyPythonDependency.PYTEST);
        writer.addDependency(SmithyPythonDependency.PYTEST_ASYNCIO);

        // Use a TreeSet to have a fixed ordering of tests.
        for (OperationShape operation : new TreeSet<>(topDownIndex.getContainedOperations(service))) {
            generateOperationTests(AppliesTo.CLIENT, operation, operationIndex);
        }
        // Write the testing implementations for various objects
        writeUtilStubs(context.symbolProvider().toSymbol(service));
    }

    private void generateOperationTests(
            AppliesTo implementation,
            OperationShape operation,
            OperationIndex operationIndex
    ) {
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
        writeTestBlock(
                testCase,
                String.format("%s_request_%s", testCase.getId(), operation.getId().getName()),
                testFilter.test(operation, testCase),
                () -> {
            var hostSplit = testCase.getHost().orElse("example.com").split("/", 2);
            var host = hostSplit[0];
            String path;
            if (hostSplit.length != 1) {
                path = hostSplit[1];
            } else {
                path = "";
            }
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.of(() -> {
                writer.write("""
                    config = $T(
                        endpoint_url="https://$L/$L",
                        http_client = $T(),
                    )
                    """,
                    CodegenUtils.getConfigSymbol(context.settings()),
                    host,
                    path,
                    REQUEST_TEST_ASYNC_HTTP_CLIENT_SYMBOL
                );
            }));

            // Generate the input using the expected shape and params
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);
            writer.write("input_ = $C\n",
                    (Runnable) () -> testCase.getParams().accept(new ValueNodeVisitor(inputShape))
            );

            // Execute the command, and catch the expected exception
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "fail", "fail");
            writer.addStdlibImport("urllib.parse", "parse_qs");
            writer.addStdlibImport("typing", "AbstractSet");
            writer.write("""
                try:
                    await client.$1T(input_)
                    fail("Expected '$2T' exception to be thrown!")
                except $2T as err:
                    actual = err.request

                    assert actual.method == $3S
                    assert actual.url.path == $4S
                    assert actual.url.host == $5S

                    query = actual.url.query
                    actual_query_segments: list[str] = query.split("&") if query else []
                    expected_query_segments: list[str] = $6J
                    for expected_query_segment in expected_query_segments:
                        assert expected_query_segment in actual_query_segments
                        actual_query_segments.remove(expected_query_segment)

                    actual_query_keys: AbstractSet[str] = parse_qs(query).keys() if query else set()
                    expected_query_keys: set[str] = set($7J)
                    assert actual_query_keys >= expected_query_keys

                    forbidden_query_keys: set[str] = set($8J)
                    for forbidden_key in forbidden_query_keys:
                        assert forbidden_key not in actual_query_keys

                    $9C
                except Exception as err:
                    fail(f"Expected '$2L' exception to be thrown, but received {type(err).__name__}: {err}")
                """,
                context.symbolProvider().toSymbol(operation),
                TEST_HTTP_SERVICE_ERR_SYMBOL,
                testCase.getMethod(),
                testCase.getUri(),
                host,
                testCase.getQueryParams(),
                testCase.getRequireQueryParams(),
                testCase.getForbidQueryParams(),
                (Runnable) () -> writer.maybeWrite(
                    !testCase.getRequireHeaders().isEmpty(),
                    "assert {h[0] for h in actual.headers} >= $J",
                    new HashSet<>(testCase.getRequireHeaders())
                )
            );
        });
    }

    private void generateResponseTest(OperationShape operation, HttpResponseTestCase testCase) {
        writeTestBlock(
                testCase,
                String.format("%s_response_%s", testCase.getId(), operation.getId().getName()),
                testFilter.test(operation, testCase),
                () -> {
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.of(() -> {
                writer.write("""
                    config = $T(
                        endpoint_url="https://example.com",
                        http_client = $T(
                            status_code = $L,
                            headers = $J,
                            body = b$S,
                        ),
                    )
                    """,
                    CodegenUtils.getConfigSymbol(context.settings()),
                    RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL,
                    testCase.getCode(),
                    CodegenUtils.toTuples(testCase.getHeaders()),
                    testCase.getBody().filter(body -> !body.isEmpty()).orElse("")
                );
            }));
            // Create an empty input object to pass
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);
            var outputShape = model.expectShape(operation.getOutputShape(), StructureShape.class);
            writer.write("input_ = $C\n",
                (Runnable) () -> (ObjectNode.builder().build()).accept(new ValueNodeVisitor(inputShape))
            );

            // Execute the command, fail if unexpected exception
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "fail", "fail");
            writer.write("""
                try:
                    actual = await client.$T(input_)
                except Exception as err:
                    fail(f"Expected a valid response, but received: {type(err).__name__}: {err}")
                else:
                    expected = $C

                    assert actual == expected
                """,
                context.symbolProvider().toSymbol(operation),
                (Runnable) () -> testCase.getParams().accept(new ValueNodeVisitor(outputShape))
            );
        });
    }

    private void generateErrorResponseTest(
            OperationShape operation,
            StructureShape error,
            HttpResponseTestCase testCase
    ) {
        writeTestBlock(testCase,
                String.format("%s_error_%s", testCase.getId(), operation.getId().getName()),
                testFilter.test(error, testCase),
                () -> {
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.of(() -> {
                writer.write("""
                    config = $T(
                        endpoint_url="https://example.com",
                        http_client = $T(
                            status_code = $L,
                            headers = $J,
                            body = b'',
                        ),
                    )
                    """,
                    CodegenUtils.getConfigSymbol(context.settings()),
                    RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL,
                    testCase.getCode(),
                    CodegenUtils.toTuples(testCase.getHeaders())
                );
            }));
            // Create an empty input object to pass
            var inputShape = model.expectShape(operation.getInputShape(), StructureShape.class);
            writer.write("input_ = $C\n",
                    (Runnable) () -> (Node.objectNode()).accept(new ValueNodeVisitor(inputShape))
            );
            // Execute the command, fail if unexpected exception
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "fail", "fail");
            writer.write("""
                try:
                    await client.$1T(input_)
                    fail("Expected '$2L' exception to be thrown!")
                except Exception as err:
                    if type(err).__name__ != $2S:
                        fail(f"Expected '$2L' exception to be thrown, but received {type(err).__name__}: {err}")
                """,
                context.symbolProvider().toSymbol(operation),
                error.getId().getName()
            );
            // TODO: Correctly assert the status code and other values
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
            writer.write("@mark.xfail()");
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

        // Set up the test http client, which is used to "handle" the requests
        writer.openBlock("client = $T(", ")\n", serviceSymbol, () -> {
            additionalConfigurator.ifPresent(Runnable::run);
        });
    }

    private void writeUtilStubs(Symbol serviceSymbol) {
        LOGGER.fine(String.format("Writing utility stubs for %s : %s", serviceSymbol.getName(), protocol.getName()));
        writer.addStdlibImport("typing", "Any");
        writer.addImports("smithy_python.interfaces.http", Set.of(
                "HeadersList", "HttpRequestConfiguration", "Request", "Response")
        );
        writer.addImport("smithy_python._private.http", "Response", "_Response");

        writer.write("""
                        class $1L($2T):
                            ""\"A test error that subclasses the service-error for protocol tests.""\"

                            def __init__(self, request: Request):
                                self.request = request


                        class $3L:
                            ""\"An asynchronous HTTP client solely for testing purposes.""\"

                            async def send(
                                self, request: Request, request_config: HttpRequestConfiguration
                            ) -> Response:
                                # Raise the exception with the request object to bypass actual request handling
                                raise $1T(request)


                        class AwaitableBody:
                            def __init__(self, contents: bytes):
                                self._contents = contents

                            async def read(self, size: int = -1) -> bytes:
                                if size < 0:
                                    result = self._contents
                                    self._contents = b''
                                    return result

                                result = self._contents[0:size-1]
                                self._contents = self._contents[size-1:]
                                return result


                        class $4L:
                            ""\"An asynchronous HTTP client solely for testing purposes.""\"

                            def __init__(self, status_code: int, headers: HeadersList, body: bytes):
                                self.status_code = status_code
                                self.headers = headers
                                self.body = AwaitableBody(body)

                            async def send(
                                self, request: Request, request_config: HttpRequestConfiguration
                            ) -> Response:
                                # Pre-construct the response from the request and return it
                                return _Response(self.status_code, self.headers, self.body)
                        """,
            TEST_HTTP_SERVICE_ERR_SYMBOL,
            CodegenUtils.getServiceError(context.settings()),
            REQUEST_TEST_ASYNC_HTTP_CLIENT_SYMBOL,
            RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL
        );
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
                var parsed = CodegenUtils.parseTimestampNode(model, inputShape, node);
                writer.writeInline(CodegenUtils.getDatetimeConstructor(writer, parsed));
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

    /**
     * Implements Python formatting for the {@code J} formatter.
     *
     * <p>Convert an Object in Java to a literal python representation.
     * The type of Object is constrained to a set of standard types in Java
     *
     * <p>For example:
     * <pre>{@code
     * List.of("a", "b") -> ["a", "b"]
     * int[] {1, 2, 3} -> (1, 2, 3)
     * Set.of("a", "b") -> {"a", "b"}
     * String "abc" -> "abc"
     * Integer 1 -> 1
     * }</pre>
     */
    private final class JavaToPythonFormatter implements BiFunction<Object, String, String> {
        @Override
        public String apply(Object type, String indent) {
            if (type instanceof List<?>) {
                return apply(((List<?>) type).stream(), ",", "[", "]", indent);
            } else if (type instanceof Object[]) {
                return apply(Stream.of((Object[]) type), ",", "(", ")", indent);
            } else if (type instanceof Set<?>) {
                return apply(((Set<?>) type).stream(), ",", "{", "}", indent);
            } else if (type instanceof Map<?, ?>) {
                return apply((Map<?, ?>) type, ",", "{", "}", indent);
            } else if (type instanceof String) {
                return writer.format("$S", type);
            } else if (type instanceof Number) {
                return writer.format("$L", type);
            } else {
                throw new CodegenException(
                        "Invalid type provided to $J: `" + type + "`");
            }
        }

        private String apply(Stream<?> stream, String sep, String start, String end, String indent) {
            return mapApply(stream, indent).collect(Collectors.joining(sep, start, end));
        }

        private String apply(Map<?, ?> map, String sep, String start, String end, String indent) {
            return map.entrySet().stream().map((entry) -> {
                return writer.format("$L: $L", apply(entry.getKey(), indent), apply(entry.getValue(), indent));
            }).collect(Collectors.joining(sep, start, end));
        }

        private Stream<String> mapApply(Stream<?> stream, String indent) {
            Set<String> test;
            return stream.map((item) -> apply(item, indent));
        }
    }
}
