/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
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
