/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
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
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.knowledge.HttpBinding.Location;
import software.amazon.smithy.model.knowledge.HttpBindingIndex;
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
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.protocoltests.traits.AppliesTo;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestsTrait;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestCase;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestsTrait;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.Pair;
import software.amazon.smithy.utils.SimpleParser;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Generates protocol tests for a given HTTP protocol.
 *
 * <p>This should preferably be instantiated and used within an
 * implementation of a `ProtocolGeneration`
 *
 * <p>See Also: <a href="https://smithy.io/2.0/additional-specs/http-protocol-compliance-tests.html#http-protocol-compliance-tests">
 * HTTP Protocol Compliance Tests</a>
 */
@SmithyUnstableApi
public final class HttpProtocolTestGenerator implements Runnable {

    private static final Logger LOGGER = Logger.getLogger(HttpProtocolTestGenerator.class.getName());
    private static final Symbol REQUEST_TEST_ASYNC_HTTP_CLIENT_SYMBOL = Symbol.builder()
            .name("RequestTestHTTPClient")
            .build();
    private static final Symbol RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL = Symbol.builder()
            .name("ResponseTestHTTPClient")
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

    /**
     * Constructor.
     *
     * @param context The code generation context.
     * @param protocol The protocol whose tests should be generated.
     * @param writer The writer to write to.
     * @param testFilter A filter that indicates tests which are expected to fail.
     */
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

    // See also: https://smithy.io/2.0/additional-specs/http-protocol-compliance-tests.html#httprequesttests-trait
    private void generateRequestTest(OperationShape operation, HttpRequestTestCase testCase) {
        writeTestBlock(
                testCase,
                String.format("%s_request_%s", testCase.getId(), operation.getId().getName()),
                testFilter.test(operation, testCase),
                () -> {
            var hostSplit = testCase.getHost().orElse("example.com").split("/", 2);
            var host = hostSplit[0];
            var resolvedHost = testCase.getResolvedHost().map(h -> h.split("/", 2)[0]).orElse(host);
            String path;
            if (hostSplit.length != 1) {
                path = hostSplit[1];
            } else {
                path = "";
            }
            writer.addImport("smithy_python._private.retries", "SimpleRetryStrategy");
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.of(() -> {
                writer.write("""
                    config = $T(
                        endpoint_uri="https://$L/$L",
                        http_client = $T(),
                        retry_strategy=SimpleRetryStrategy(max_attempts=1),
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
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "fail");
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "raises");
            writer.addStdlibImport("urllib.parse", "parse_qsl");
            writer.write("""
                try:
                    await client.$1T(input_)
                    fail("Expected '$2T' exception to be thrown!")
                except $2T as err:
                    actual = err.request

                    assert actual.method == $3S
                    assert actual.destination.path == $4S
                    assert actual.destination.host == $5S

                    query = actual.destination.query
                    actual_query_segments: list[str] = query.split("&") if query else []
                    expected_query_segments: list[str] = $6J
                    for expected_query_segment in expected_query_segments:
                        assert expected_query_segment in actual_query_segments
                        actual_query_segments.remove(expected_query_segment)

                    actual_query_keys: list[str] = [k.lower() for k, v in parse_qsl(query)]
                    forbidden_query_keys: set[str] = set($7J)
                    for forbidden_key in forbidden_query_keys:
                        assert forbidden_key.lower() not in actual_query_keys

                    required_query_keys: list[str] = $8J
                    for required_query_key in required_query_keys:
                        assert required_query_key.lower() in actual_query_keys
                        # These are removed because the required list could require more than one
                        # value. By removing each value after we assert that it's there, we can
                        # effectively validate that without having to have a more complex comparator.
                        actual_query_keys.remove(required_query_key)

                    expected_headers: list[tuple[str, str]] = [
                        ${9C|}
                    ]
                    for expected_key, expected_val in expected_headers:
                        assert expected_val in actual.fields.get_field(expected_key).values

                    forbidden_headers: set[str] = set($10J)
                    for forbidden_key in forbidden_headers:
                        with raises(KeyError):
                            actual.fields.get_field(forbidden_key)

                    required_headers: list[str] = $11J
                    for required_key in required_headers:
                        # Fields.remove_field() raises KeyError if key does not exist
                        actual.fields.remove_field(required_key)

                    ${12C|}

                except Exception as err:
                    fail(f"Expected '$2L' exception to be thrown, but received {type(err).__name__}: {err}")
                """,
                context.symbolProvider().toSymbol(operation),
                TEST_HTTP_SERVICE_ERR_SYMBOL,
                testCase.getMethod(),
                testCase.getUri(),
                resolvedHost,
                testCase.getQueryParams(),
                toLowerCase(testCase.getForbidQueryParams()),
                toLowerCase(testCase.getRequireQueryParams()),
                (Runnable) () -> writeExpectedHeaders(testCase, operation),
                toLowerCase(testCase.getForbidHeaders()),
                toLowerCase(testCase.getRequireHeaders()),
                writer.consumer(w -> writeRequestBodyComparison(testCase, w))
            );
        });
    }

    private List<String> toLowerCase(List<String> given) {
        return given.stream().map(str -> str.toLowerCase(Locale.US)).collect(Collectors.toList());
    }

    private void writeExpectedHeaders(
        HttpRequestTestCase testCase,
        OperationShape operation
    ) {
        var headerPairs = splitHeaders(testCase, operation);
        for (Pair<String, String> pair : headerPairs) {
            writer.write("($S, $S),", pair.getKey().toLowerCase(Locale.US), pair.getValue());
        }
    }

    // TODO: upstream this to Smithy itself or update the protocol test traits
    private List<Pair<String, String>> splitHeaders(
        HttpRequestTestCase testCase,
        OperationShape operation
    ) {
        // Get a map of headers to binding info for headers that are bound to lists.
        var listBindings = HttpBindingIndex.of(model)
            .getRequestBindings(operation, Location.HEADER)
            .stream()
            .filter(binding -> model.expectShape(binding.getMember().getTarget()).isListShape())
            .collect(Collectors.toMap(HttpBinding::getLocationName, binding -> binding));

        // Go through each of the headers on the protocol test and turn them into key-value tuples.
        var headerPairs = new ArrayList<Pair<String, String>>();
        for (Map.Entry<String, String> entry : testCase.getHeaders().entrySet()) {
            // If we know a list isn't bound to this header, then we know it's static so we can just
            // add it directly.
            if (!listBindings.containsKey(entry.getKey())) {
                headerPairs.add(Pair.of(entry.getKey(), entry.getValue()));
                continue;
            }
            var binding = listBindings.get(entry.getKey());
            var paramValue = testCase.getParams().expectArrayMember(binding.getMemberName());
            if (paramValue.size() == 1) {
                // If it's a single value of a list, we want to keep it as-is.
                headerPairs.add(Pair.of(entry.getKey(), entry.getValue()));
            }
            try {
                headerPairs.addAll(splitHeader(binding, entry.getKey(), entry.getValue()));
            } catch (Exception e) {
                throw new CodegenException(
                    String.format("Failed to split header in protocol test %s - `%s`: `%s` - %s",
                        testCase.getId(), entry.getKey(), entry.getValue(), e));
            }
        }

        return headerPairs;
    }

    private List<Pair<String, String>> splitHeader(HttpBinding binding, String key, String value) {
        var values = new ArrayList<Pair<String, String>>();
        var parser = new SimpleParser(value);

        boolean isHttpDateMember = false;
        var listShape = model.expectShape(binding.getMember().getTarget(), ListShape.class);
        var listMember = model.expectShape(listShape.getMember().getTarget());
        if (listMember.isTimestampShape()) {
            var httpIndex = HttpBindingIndex.of(model);
            var format = httpIndex.determineTimestampFormat(
                binding.getMember(), binding.getLocation(), Format.HTTP_DATE);
            isHttpDateMember = format == Format.HTTP_DATE;
        }

        // Strip any leading whitespace
        parser.ws();
        while (!parser.eof()) {
            values.add(Pair.of(key, parseEntry(parser, isHttpDateMember)));
        }
        return values;
    }

    private String parseEntry(SimpleParser parser, boolean skipFirstComma) {
        String value;

        // If the first character is a dquote, parse as a quoted string.
        if (parser.peek() == '"') {
            parser.expect('"');
            var builder = new StringBuilder();
            while (!parser.eof() && parser.peek() != '"') {
                if (parser.peek() == '\\') {
                    parser.skip();
                }
                builder.append(parser.peek());
                parser.skip();
            }
            // Ensure that the string ends in a dquote
            parser.expect('"');
            value = builder.toString();
        } else {
            var start = parser.position();
            parser.consumeUntilNoLongerMatches(character -> character != ',');
            if (skipFirstComma) {
                parser.expect(',');
                parser.consumeUntilNoLongerMatches(character -> character != ',');
            }
            // We can use substring instead of a StringBuilder here because we don't
            // need to worry about escaped characters.
            value = parser.expression().substring(start, parser.position()).trim();
        }

        // Strip trailing whitespace
        parser.ws();

        // If we're not at the end of the line, assert that we encounter a comma.
        if (!parser.eof()) {
            parser.expect(',');
            parser.ws();
        }

        return value;
    }

    private void writeRequestBodyComparison(HttpMessageTestCase testCase, PythonWriter writer) {
        if (testCase.getBody().isEmpty()) {
            return;
        }
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
        writer.write("actual_body_content = await AsyncBytesReader(actual.body).read()");
        writer.write("expected_body_content = b$S", testCase.getBody().get());
        compareMediaBlob(testCase, writer);
    }

    private void compareMediaBlob(HttpMessageTestCase testCase, PythonWriter writer) {
        var contentType = testCase.getBodyMediaType().orElse("application/octet-stream");
        if (contentType.equals("application/json") || contentType.endsWith("+json")) {
            writer.addStdlibImport("json");
            writer.write("""
                actual_body = json.loads(actual_body_content) if actual_body_content else ""
                expected_body = json.loads(expected_body_content)
                assert actual_body == expected_body

                """);
            return;
        }
        writer.write("assert actual_body_content == expected_body_content\n");
    }

    // See also: https://smithy.io/2.0/additional-specs/http-protocol-compliance-tests.html#httpresponsetests-trait
    private void generateResponseTest(OperationShape operation, HttpResponseTestCase testCase) {
        writeTestBlock(
                testCase,
                String.format("%s_response_%s", testCase.getId(), operation.getId().getName()),
                testFilter.test(operation, testCase),
                () -> {
            writeClientBlock(context.symbolProvider().toSymbol(service), testCase, Optional.of(() -> {
                writer.write("""
                    config = $T(
                        endpoint_uri="https://example.com",
                        http_client = $T(
                            status=$L,
                            headers=$J,
                            body=b$S,
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

                    ${C|}
                """,
                context.symbolProvider().toSymbol(operation),
                (Runnable) () -> testCase.getParams().accept(new ValueNodeVisitor(outputShape)),
                (Runnable) () -> assertResponseEqual(testCase, operation)
            );
        });
    }

    // See also: https://smithy.io/2.0/additional-specs/http-protocol-compliance-tests.html#httpresponsetests-trait
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
                        endpoint_uri="https://example.com",
                        http_client = $T(
                            status=$L,
                            headers=$J,
                            body=b$S,
                        ),
                    )
                    """,
                    CodegenUtils.getConfigSymbol(context.settings()),
                    RESPONSE_TEST_ASYNC_HTTP_CLIENT_SYMBOL,
                    testCase.getCode(),
                    CodegenUtils.toTuples(testCase.getHeaders()),
                    testCase.getBody().orElse("")
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

    private void assertResponseEqual(HttpMessageTestCase testCase, Shape operationOrError) {
        var index = HttpBindingIndex.of(context.model());
        var streamBinding = index.getResponseBindings(operationOrError, Location.PAYLOAD)
            .stream()
            .filter(binding -> binding.getMember().getMemberTrait(context.model(), StreamingTrait.class).isPresent())
            .findAny();

        if (streamBinding.isEmpty()) {
            writer.write("assert actual == expected\n");
            return;
        }

        StructureShape responseShape = operationOrError.asStructureShape().orElseGet(() -> {
            var operation = operationOrError.asOperationShape().get();
            return context.model().expectShape(operation.getOutputShape(), StructureShape.class);
        });

        var streamingMember = streamBinding.get().getMember();

        for (MemberShape member : responseShape.members()) {
            var memberName = context.symbolProvider().toMemberName(member);
            if (member.equals(streamingMember)) {
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python.interfaces.blobs", "AsyncByteStream");
                writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
                writer.write("""
                    assert isinstance(actual.$1L, AsyncByteStream)
                    actual_body_content = await actual.$1L.read()
                    expected_body_content = await AsyncBytesReader(expected.$1L).read()
                    """, memberName);
                compareMediaBlob(testCase, writer);
                continue;
            }
            writer.write("assert actual.$1L == expected.$1L\n", memberName);
        }
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
        writer.addImport("smithy_python.interfaces", "Fields");
        writer.addImports("smithy_python.interfaces.http", Set.of(
                "HTTPRequestConfiguration", "HTTPRequest", "HTTPResponse")
        );
        writer.addImport("smithy_python._private", "tuples_to_fields");
        writer.addImport("smithy_python._private.http", "HTTPResponse", "_HTTPResponse");
        writer.addImport("smithy_python.async_utils", "async_list");

        writer.write("""
                        class $1L($2T):
                            ""\"A test error that subclasses the service-error for protocol tests.""\"

                            def __init__(self, request: HTTPRequest):
                                self.request = request


                        class $3L:
                            ""\"An asynchronous HTTP client solely for testing purposes.""\"

                            async def send(
                                self, *, request: HTTPRequest, request_config: HTTPRequestConfiguration | None
                            ) -> HTTPResponse:
                                # Raise the exception with the request object to bypass actual request handling
                                raise $1T(request)


                        class $4L:
                            ""\"An asynchronous HTTP client solely for testing purposes.""\"

                            def __init__(self, status: int, headers: list[tuple[str, str]], body: bytes):
                                self.status = status
                                self.fields = tuples_to_fields(headers)
                                self.body = body

                            async def send(
                                self, *, request: HTTPRequest, request_config: HTTPRequestConfiguration | None
                            ) -> _HTTPResponse:
                                # Pre-construct the response from the request and return it
                                return _HTTPResponse(
                                    status=self.status,
                                    fields=self.fields,
                                    body=async_list([self.body]),
                                )
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
