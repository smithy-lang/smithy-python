/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.EndpointTrait;
import software.amazon.smithy.python.codegen.generators.ConfigGenerator;
import software.amazon.smithy.python.codegen.generators.EndpointBddGenerator;
import software.amazon.smithy.python.codegen.integrations.EndpointRulesExtension;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.rulesengine.language.syntax.parameters.Parameter;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.rulesengine.traits.EndpointTestCase;
import software.amazon.smithy.rulesengine.traits.EndpointTestExpectation;
import software.amazon.smithy.rulesengine.traits.EndpointTestOperationInput;
import software.amazon.smithy.rulesengine.traits.EndpointTestsTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates {@code tests/test_endpoints.py} from a service's {@code smithy.rules#endpointTests}
 * cases.
 *
 * <p>Every case becomes a rules test, which resolves the case's parameter values with the
 * client's own endpoint resolver. Every operation input of a case also becomes a client test,
 * which calls the operation through the client with config from the input's built-in and
 * client parameters and checks the endpoint the client resolves. A client test the client
 * can't express is generated as skipped, with the reason. Cases keep the trait's {@code params}
 * and {@code expect} objects as they are.
 */
@SmithyInternalApi
public final class EndpointTestGenerator implements Runnable {

    private static final Symbol CHECK_RULES_CASE = testSymbol("check_rules_case_async");
    private static final Symbol CHECK_CLIENT_CASE = testSymbol("check_client_case_async");

    private final GenerationContext context;
    private final ServiceShape service;
    private final Map<String, Parameter> parametersByBuiltIn = new HashMap<>();
    private final Map<String, ConfigProperty> clientContextFields;
    private final List<EndpointRulesExtension> rulesExtensions;

    /**
     * @param context The generation context.
     */
    public EndpointTestGenerator(GenerationContext context) {
        this.context = context;
        this.service = context.settings().service(context.model());
        service.getTrait(EndpointBddTrait.class).ifPresent(bdd -> {
            for (Parameter parameter : bdd.getParameters()) {
                parameter.getBuiltIn().ifPresent(builtIn -> parametersByBuiltIn.put(builtIn, parameter));
            }
        });
        this.clientContextFields = ConfigGenerator.clientContextFields(context);
        this.rulesExtensions = ConfigGenerator.endpointRulesExtensions(context);
    }

    @Override
    public void run() {
        var cases = service.getTrait(EndpointTestsTrait.class)
                .map(EndpointTestsTrait::getTestCases)
                .orElse(List.of());
        if (cases.isEmpty() || !service.hasTrait(EndpointBddTrait.class)) {
            return;
        }
        context.writerDelegator().useFileWriter("./tests/test_endpoints.py", "tests.test_endpoints", writer -> {
            writer.addDependency(SmithyPythonDependency.PYTEST);
            writer.addDependency(SmithyPythonDependency.PYTEST_ASYNCIO);
            writer.addDependency(SmithyPythonDependency.SMITHY_TEST);
            writer.addStdlibImport("collections.abc", "Mapping");
            writer.addStdlibImport("typing", "Any");
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "mark");
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "param");
            writeClientFactory(writer);
            writeRulesExtensions(writer);
            writeRulesTests(writer, cases);
            writeClientTests(writer, cases);
        });
    }

    // _config builds the client's config with the test config, _endpoint_resolver gets one
    // default endpoint resolver for every rules test, and _client builds a client with an
    // interceptor added to it.
    private void writeClientFactory(PythonWriter writer) {
        var settings = context.settings();
        var asyncConfig = CodegenUtils.getAsyncConfigSymbol(settings, context.model());
        var config = asyncConfig.orElse(CodegenUtils.getConfigSymbol(settings));
        var construct = asyncConfig.isPresent()
                ? writer.format("await $T.resolve", config)
                : writer.format("$T", config);
        var client = context.symbolProvider().toSymbol(service);
        writer.write("""
                # Endpoint tests from the endpointTests trait of $L.

                _TEST_CONFIG: dict[str, Any] = {
                    ${C|}
                }


                async def _config(**fields: Any) -> $T:
                    return $L(
                        **(_TEST_CONFIG | fields),
                        retry_strategy=$T(max_attempts=1),
                    )


                # Every rules test shares one resolver, so its caches see changing parameters.
                _resolver: $T | None = None


                async def _endpoint_resolver() -> $T:
                    global _resolver
                    if _resolver is None:
                        config = await _config()
                        # Only the resolver is used, so the transport is closed right away.
                        await $T(config.transport)
                        assert config.endpoint_resolver is not None
                        _resolver = config.endpoint_resolver
                    return _resolver


                async def _client(
                    config: Mapping[str, Any], capture: $T[Any, Any, Any, Any]
                ) -> $T:
                    return $T(config=await _config(**config, interceptors=[capture]))
                """,
                service.getId(),
                writer.consumer(w -> {
                    for (EndpointRulesExtension extension : rulesExtensions) {
                        extension.writeEndpointTestConfig(context, w);
                    }
                    // Explicit values keep client context fields from being read from the
                    // environment.
                    for (ConfigProperty field : clientContextFields.values()) {
                        if (field.resolver().isPresent()) {
                            w.write("$S: None,", field.name());
                        }
                    }
                }),
                config,
                construct,
                RuntimeTypes.SIMPLE_RETRY_STRATEGY,
                RuntimeTypes.ENDPOINT_RESOLVER,
                RuntimeTypes.ENDPOINT_RESOLVER,
                RuntimeTypes.ASYNC_CLOSE,
                RuntimeTypes.INTERCEPTOR,
                client,
                client);
    }

    // _RULES_EXTENSIONS lets the checks build the auth schemes a case expects the way the
    // client's endpoint resolver builds them.
    private void writeRulesExtensions(PythonWriter writer) {
        if (rulesExtensions.isEmpty()) {
            return;
        }
        writer.write("""


                _RULES_EXTENSIONS = [
                    ${C|}
                ]
                """,
                writer.consumer(w -> {
                    for (EndpointRulesExtension extension : rulesExtensions) {
                        w.write("$T,", extension.getRulesExtensionSymbol(context));
                    }
                }));
    }

    private String extensionsArgument() {
        return rulesExtensions.isEmpty() ? "" : ", extensions=_RULES_EXTENSIONS";
    }

    private void writeRulesTests(PythonWriter writer, List<EndpointTestCase> cases) {
        var ids = new CaseIds();
        writer.write("""


                RULES_CASES = [
                    ${C|}
                ]


                @mark.parametrize(("params", "expect"), RULES_CASES)
                async def test_endpoint_rules(params: dict[str, Any], expect: dict[str, Any]) -> None:
                    await $T(await _endpoint_resolver(), params, expect$L)
                """,
                writer.consumer(w -> {
                    for (EndpointTestCase testCase : cases) {
                        w.write("""
                                param(
                                    $L,
                                    $L,
                                    id=$S,
                                ),""",
                                literal(testCase.getParams()),
                                expectation(testCase.getExpect()),
                                ids.next(testCase));
                    }
                }),
                CHECK_RULES_CASE,
                extensionsArgument());
    }

    private void writeClientTests(PythonWriter writer, List<EndpointTestCase> cases) {
        if (cases.stream().allMatch(testCase -> testCase.getOperationInputs().isEmpty())) {
            return;
        }
        writer.addStdlibImport("collections.abc", "Awaitable");
        writer.addStdlibImport("collections.abc", "Callable");
        var client = context.symbolProvider().toSymbol(service);
        var ids = new CaseIds();
        writer.write("""


                CLIENT_CASES = [
                    ${C|}
                ]


                @mark.parametrize(("config", "operation", "input", "expect"), CLIENT_CASES)
                async def test_endpoint_client(
                    config: dict[str, Any],
                    operation: Callable[[$T, Any], Awaitable[Any]],
                    input: Any,
                    expect: dict[str, Any],
                ) -> None:
                    await $T(lambda capture: _client(config, capture), operation, input, expect$L)
                """,
                writer.consumer(w -> {
                    for (EndpointTestCase testCase : cases) {
                        for (EndpointTestOperationInput input : testCase.getOperationInputs()) {
                            writeClientCase(w, testCase, input, ids.next(testCase));
                        }
                    }
                }),
                client,
                CHECK_CLIENT_CASE,
                extensionsArgument());
    }

    private void writeClientCase(
            PythonWriter writer,
            EndpointTestCase testCase,
            EndpointTestOperationInput input,
            String id
    ) {
        var operation = operation(input.getOperationName());
        var inputShape = context.model().expectShape(operation.getInputShape(), StructureShape.class);
        var skips = new ArrayList<String>();
        var entries = configEntries(input, skips);
        writer.write("""
                param(
                    {
                        ${C|}
                    },
                    $T.$L,
                    ${C|},
                    $L,
                    id=$S,$L
                ),""",
                writer.consumer(w -> entries.forEach(entry -> entry.accept(w))),
                context.symbolProvider().toSymbol(service),
                context.symbolProvider()
                        .toSymbol(operation)
                        .expectProperty(SymbolProperties.OPERATION_METHOD)
                        .getName(),
                writer.consumer(w -> input.getOperationParams()
                        .accept(new ValueNodeVisitor(context, w, inputShape))),
                expectation(testCase.getExpect()),
                id,
                marks(writer, operation, skips));
    }

    // A skip for a case the client can't express, or an expected failure for a known gap.
    private static String marks(PythonWriter writer, OperationShape operation, List<String> skips) {
        if (!skips.isEmpty()) {
            return writer.format("\n    marks=mark.skip(reason=$S),", String.join("; ", skips));
        }
        var hostLabels = operation.getTrait(EndpointTrait.class)
                .map(trait -> !trait.getHostPrefix().getLabels().isEmpty())
                .orElse(false);
        if (hostLabels) {
            return writer.format("\n    marks=mark.xfail(reason=$S, strict=True),",
                    "Host labels in an endpoint trait's hostPrefix aren't serialized yet");
        }
        return "";
    }

    // The config entries an operation input's built-in and client parameters set. A parameter
    // the client has no config field for adds the reason the case is skipped.
    private List<Consumer<PythonWriter>> configEntries(EndpointTestOperationInput input, List<String> skips) {
        var entries = new ArrayList<Consumer<PythonWriter>>();
        input.getBuiltInParams().getMembers().forEach((name, value) -> {
            var builtIn = name.getValue();
            var entry = builtInEntry(builtIn, value);
            if (entry.isPresent()) {
                entries.add(entry.get());
                return;
            }
            var parameter = parametersByBuiltIn.get(builtIn);
            boolean isDefault = parameter == null
                    || parameter.getDefault().map(d -> d.toNode().equals(value)).orElse(false);
            if (!isDefault) {
                skips.add("No config field sets the built-in " + builtIn);
            }
        });
        input.getClientParams().getMembers().forEach((name, value) -> {
            var field = clientContextFields.get(name.getValue());
            if (field != null) {
                entries.add(entry(field.name(), value));
            } else {
                skips.add(name.getValue() + " is not a client context parameter");
            }
        });
        return entries;
    }

    private Optional<Consumer<PythonWriter>> builtInEntry(String builtIn, Node value) {
        var parameter = parametersByBuiltIn.get(builtIn);
        // A built-in that is also a client context parameter is read from its config field.
        var field = parameter == null ? null : clientContextFields.get(parameter.getNameString());
        if (field != null) {
            return Optional.of(entry(field.name(), value));
        }
        if (builtIn.equals("SDK::Endpoint")) {
            return Optional.of(entry("endpoint_uri", value));
        }
        for (EndpointRulesExtension extension : rulesExtensions) {
            var entry = extension.getEndpointTestBuiltIn(context, builtIn, value);
            if (entry.isPresent()) {
                return entry;
            }
        }
        return Optional.empty();
    }

    private static Consumer<PythonWriter> entry(String field, Node value) {
        return writer -> writer.write("$S: $L,", field, literal(value));
    }

    private OperationShape operation(String name) {
        return TopDownIndex.of(context.model())
                .getContainedOperations(service)
                .stream()
                .filter(operation -> operation.getId().getName().equals(name))
                .findFirst()
                .orElseThrow(() -> new CodegenException(String.format(
                        "Endpoint test operation %s is not in service %s",
                        name,
                        service.getId())));
    }

    // The case's expect object as the trait models it.
    private static String expectation(EndpointTestExpectation expect) {
        var error = expect.getError();
        if (error.isPresent()) {
            return literal(Node.objectNode().withMember("error", error.get()));
        }
        var endpoint = expect.getEndpoint()
                .orElseThrow(() -> new CodegenException("An endpoint test case expects neither an endpoint"
                        + " nor an error"));
        var expected = Node.objectNodeBuilder().withMember("url", endpoint.getUrl());
        if (!endpoint.getHeaders().isEmpty()) {
            var headers = Node.objectNodeBuilder();
            endpoint.getHeaders().forEach((name, values) -> headers.withMember(name, Node.fromStrings(values)));
            expected.withMember("headers", headers.build());
        }
        if (!endpoint.getProperties().isEmpty()) {
            var properties = Node.objectNodeBuilder();
            endpoint.getProperties().forEach(properties::withMember);
            expected.withMember("properties", properties.build());
        }
        return literal(Node.objectNode().withMember("endpoint", expected.build()));
    }

    /**
     * Renders a node as a Python literal on one line: lists for arrays and dicts for objects.
     *
     * @param node The node.
     * @return Returns the Python literal.
     */
    public static String literal(Node node) {
        return switch (node.getType()) {
            case NULL -> "None";
            case BOOLEAN -> node.expectBooleanNode().getValue() ? "True" : "False";
            case NUMBER -> node.expectNumberNode().getValue().toString();
            case STRING -> EndpointBddGenerator.literal(node.expectStringNode().getValue());
            case ARRAY -> node.expectArrayNode()
                    .getElements()
                    .stream()
                    .map(EndpointTestGenerator::literal)
                    .collect(Collectors.joining(", ", "[", "]"));
            case OBJECT -> node.expectObjectNode()
                    .getMembers()
                    .entrySet()
                    .stream()
                    .map(member -> EndpointBddGenerator.literal(member.getKey().getValue()) + ": "
                            + literal(member.getValue()))
                    .collect(Collectors.joining(", ", "{", "}"));
        };
    }

    private static Symbol testSymbol(String name) {
        return Symbol.builder()
                .name(name)
                .namespace(SmithyPythonDependency.SMITHY_TEST.packageName() + ".aio", ".")
                .addDependency(SmithyPythonDependency.SMITHY_TEST)
                .build();
    }

    // Test ids from case documentation, numbered when a description repeats.
    private static final class CaseIds {
        private final Set<String> used = new HashSet<>();

        String next(EndpointTestCase testCase) {
            var base = testCase.getDocumentation().orElse("undocumented");
            var id = base;
            for (int n = 2; !used.add(id); n++) {
                id = base + " (" + n + ")";
            }
            return id;
        }
    }
}
