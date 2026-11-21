/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.PaginatedTrait;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

/**
 * Generates the client of pagination.smithy and checks its paginators by using
 * them, offline, from Python. Also checks the typing of a client named like the
 * type of its paginator's items.
 */
public class PaginationCodegenTest {

    @Test
    public void generatesPaginators(@TempDir Path tempDir) throws Exception {
        generate(loadModel(), tempDir, "example.pages#Paginator", "pages");
        assertChecksPass(tempDir);
    }

    // The client is named like the type of its items, which is imported from outside
    // the models module: the items are still of the imported type.
    @Test
    public void itemTypeNamedLikeClient(@TempDir Path tempDir) throws Exception {
        var loader = PaginationCodegenTest.class.getClassLoader();
        var model = Model.assembler(loader)
                .discoverModels(loader)
                .addUnparsedModel("items.smithy", """
                        $version: "2.0"
                        namespace example.items
                        use aws.protocols#restJson1
                        @restJson1
                        service Decimal { version: "1", operations: [Fetch] }
                        @paginated(inputToken: "token", outputToken: "token", items: "values")
                        @http(method: "POST", uri: "/")
                        operation Fetch {
                            input := { token: String }
                            output := { token: String, values: Values }
                        }
                        list Values { member: BigDecimal }
                        """)
                .assemble()
                .unwrap();
        generate(model, tempDir, "example.items#Decimal", "items");
        var client = Files.readString(tempDir.resolve("src/items/client.py"));
        assertTrue(client.contains("from decimal import Decimal as _Decimal\n")
                && client.contains("-> ItemPaginator[_models.FetchOutput, _Decimal]:"), client);
        Files.writeString(tempDir.resolve("src/items_consumer.py"), """
                import decimal
                from collections.abc import AsyncIterator, Iterator
                from typing import assert_type

                from items import AsyncDecimal, Decimal


                def use(client: Decimal) -> None:
                    assert_type(client.paginate_fetch().items(), Iterator[decimal.Decimal])


                def use_async(client: AsyncDecimal) -> None:
                    assert_type(
                        client.paginate_fetch().items(), AsyncIterator[decimal.Decimal]
                    )
                """);
        assertSucceeds(tempDir,
                "python3",
                "-m",
                "pyright",
                "src/items_consumer.py",
                "src/items/client.py",
                "src/items/aio/client.py");
    }

    // A valid model, assembled and validated, whose Fetch pagination each case then
    // changes through shape builders, which don't validate: so the generator, not the
    // assembler, must reject the configuration.
    private static final String LIMITS = """
            $version: "2.0"
            namespace example.limits
            use aws.protocols#restJson1
            @restJson1
            service Limits { version: "1", operations: [Fetch, Plain] }
            @paginated(inputToken: "token", outputToken: "token", pageSize: "size", items: "values")
            @http(method: "POST", uri: "/fetch")
            operation Fetch {
                input := { token: String, size: Integer, label: String, count: Integer }
                output := { token: String, values: Values, label: String, count: Integer, tokens: Tokens }
            }
            @http(method: "POST", uri: "/plain")
            operation Plain {
                input := { name: String }
                output := { name: String }
            }
            list Values { member: String }
            map Tokens { key: String, value: String }
            """;
    private static final ShapeId FETCH = ShapeId.from("example.limits#Fetch");
    private static final ShapeId LIMITS_SERVICE = ShapeId.from("example.limits#Limits");

    // Fetch's valid settings, for a case to change one of.
    private static PaginatedTrait.Builder fetch() {
        return PaginatedTrait.builder().inputToken("token").outputToken("token").pageSize("size").items("values");
    }

    static Stream<Arguments> invalidPagination() {
        return Stream.of(
                Arguments.of("unresolved pageSize", "pageSize", fetch().pageSize("missing").build(), null),
                Arguments.of("nonintegral pageSize", "pageSize", fetch().pageSize("label").build(), null),
                Arguments.of("unresolved items", "items", fetch().items("missing").build(), null),
                Arguments.of("scalar items", "items", fetch().items("label").build(), null),
                Arguments.of("integer inputToken", "inputToken", fetch().inputToken("count").build(), null),
                Arguments.of("integer outputToken", "outputToken", fetch().outputToken("count").build(), null),
                // Each output token is sent as the next input token, unconverted, so
                // a string input token can't take a map output token.
                Arguments.of("map outputToken for string inputToken",
                        "outputToken",
                        fetch().outputToken("tokens").build(),
                        null),
                // Fetch sets no page size, so it takes the service's.
                Arguments.of("inherited unresolved pageSize",
                        "pageSize",
                        PaginatedTrait.builder().inputToken("token").outputToken("token").items("values").build(),
                        PaginatedTrait.builder().pageSize("missing").build()));
    }

    // A configured setting that doesn't resolve to a member of a supported type fails
    // generation, naming the operation and the setting, rather than disappearing.
    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidPagination")
    public void rejectsInvalidPagination(
            String label,
            String setting,
            PaginatedTrait operationTrait,
            PaginatedTrait serviceTrait,
            @TempDir Path tempDir
    ) {
        var model = limits(operationTrait, serviceTrait);
        var error = assertThrows(CodegenException.class,
                () -> generate(model, tempDir, LIMITS_SERVICE.toString(), "limits"));
        var message = String.valueOf(error.getMessage());
        assertTrue(message.contains(FETCH.toString()) && message.contains(setting), message);
    }

    // The service's settings apply only to operations that opt in, and an
    // operation's own settings override them.
    @Test
    public void honorsOptInAndOverrides(@TempDir Path tempDir) throws Exception {
        var service = PaginatedTrait.builder()
                .inputToken("missing")
                .outputToken("missing")
                .pageSize("missing")
                .items("missing")
                .build();
        generate(limits(fetch().build(), service), tempDir, LIMITS_SERVICE.toString(), "limits");
        var client = Files.readString(tempDir.resolve("src/limits/client.py"));
        assertTrue(client.contains("def paginate_fetch(") && !client.contains("paginate_plain"), client);
    }

    private static Model limits(PaginatedTrait operationTrait, PaginatedTrait serviceTrait) {
        var loader = PaginationCodegenTest.class.getClassLoader();
        var model = Model.assembler(loader)
                .discoverModels(loader)
                .addUnparsedModel("limits.smithy", LIMITS)
                .assemble()
                .unwrap();
        var builder = model.toBuilder();
        builder.addShape(model.expectShape(FETCH, OperationShape.class)
                .toBuilder()
                .addTrait(operationTrait)
                .build());
        if (serviceTrait != null) {
            builder.addShape(model.expectShape(LIMITS_SERVICE, ServiceShape.class)
                    .toBuilder()
                    .addTrait(serviceTrait)
                    .build());
        }
        return builder.build();
    }

    private static Model loadModel() {
        var loader = PaginationCodegenTest.class.getClassLoader();
        return Model.assembler(loader)
                .discoverModels(loader)
                .addImport(PaginationCodegenTest.class.getResource("pagination.smithy"))
                .assemble()
                .unwrap();
    }

    private static void generate(Model model, Path directory, String service, String module) {
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(directory))
                .settings(ObjectNode.builder()
                        .withMember("service", service)
                        .withMember("module", module)
                        .withMember("moduleVersion", "0.0.1")
                        .build())
                .model(model)
                .build();
        new PythonClientCodegenPlugin().execute(context);
    }

    private static void assertChecksPass(Path directory) throws Exception {
        var script = Path.of(PaginationCodegenTest.class.getResource("pagination_check.py").toURI());
        assertSucceeds(null, "python3", script.toString(), directory.toString());
    }

    private static void assertSucceeds(Path directory, String... command) throws Exception {
        var process = new ProcessBuilder(command)
                .directory(directory == null ? null : directory.toFile())
                .redirectErrorStream(true)
                .start();
        var output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertTrue(process.waitFor(300, TimeUnit.SECONDS), String.join(" ", command) + " timed out");
        System.out.println(output);
        assertEquals(0, process.exitValue(), output);
    }
}
