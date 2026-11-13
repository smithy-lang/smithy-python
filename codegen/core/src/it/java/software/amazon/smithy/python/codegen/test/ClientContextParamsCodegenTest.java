/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

public class ClientContextParamsCodegenTest {

    @Test
    public void addsConfigFieldsForClientContextParams(@TempDir Path tempDir) throws IOException {
        generate(tempDir);

        var config = Files.readString(tempDir.resolve("src/ccp/config.py"));
        // Named to_snake_case(name), typed from the trait, documented from it, defaulting to None.
        assertTrue(config.contains("force_path_style: bool | None"));
        assertTrue(config.contains("Forces path-style addressing."));
        assertTrue(config.contains("disable_s3_express_session_auth: bool | None"));
        assertTrue(config.contains("The DisableS3ExpressSessionAuth endpoint parameter."));
        assertTrue(config.contains("stage: str | None"));
        assertTrue(config.contains("The deployment stage."));
        assertTrue(config.contains("force_path_style: bool | None = None,"));
        assertTrue(config.contains("self.force_path_style = force_path_style"));

        var endpoints = Files.readString(tempDir.resolve("src/ccp/_private/endpoints.py"));
        assertTrue(endpoints.contains("(\"ForcePathStyle\", \"boolean\", True, False, None, \"force_path_style\")"));
        assertTrue(endpoints.contains("(\"Stage\", \"string\", False, None, None, \"stage\")"));
    }

    @Test
    public void endpointTestsCallOperationsWithKeywordArguments(@TempDir Path tempDir) throws IOException {
        generate(tempDir);

        var tests = Files.readString(tempDir.resolve("tests/test_endpoints.py"));
        // A client case gives the operation's input as the keyword arguments of the call,
        // keyed by parameter name, so a member named like one of the method's own
        // parameters has its escaped name. Nested values are models.
        assertGenerated(tests, """
                param(
                    {
                        "stage": "beta",
                    },
                    AsyncClientContextService.put_thing,
                    {
                        "name": "n",
                        "tag": ThingTag(
                            key="k",
                        ),
                        "plugins_": [
                            "p",
                        ],
                    },
                    {"endpoint": {"url": "https://beta.example.com"}},
                    id="Stage from config",
                ),
                """);
        // An operation without input members is called with no keyword arguments.
        assertGenerated(tests, """
                param(
                    {
                        "stage": "beta",
                    },
                    AsyncClientContextService.ping,
                    {},
                    {"endpoint": {"url": "https://beta.example.com"}},
                    id="Stage from config (2)",
                )
                """);
        // The test hands the arguments to the check, which unpacks them into the call.
        assertGenerated(tests, """
                async def test_endpoint_client(
                    config: dict[str, Any],
                    operation: Callable[Concatenate[AsyncClientContextService, ...], Awaitable[Any]],
                    input: dict[str, Any],
                    expect: dict[str, Any],
                ) -> None:
                    await check_client_case_async(lambda capture: _client(config, capture), operation, input, expect)
                """);
        // No input object is built, since the client methods don't take one.
        assertFalse(tests.contains("PutThingInput"), tests);
        assertFalse(tests.contains("PingInput"), tests);
    }

    private static void generate(Path tempDir) {
        var loader = ClientContextParamsCodegenTest.class.getClassLoader();
        Model model = Model.assembler(loader)
                .discoverModels(loader)
                .addImport(ClientContextParamsCodegenTest.class.getResource("client-context-params.smithy"))
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(ObjectNode.builder()
                        .withMember("service", "example.ccp#ClientContextService")
                        .withMember("module", "ccp")
                        .withMember("moduleVersion", "0.0.1")
                        .build())
                .model(model)
                .build();
        new PythonClientCodegenPlugin().execute(context);
    }

    // Compares ignoring layout, so the assertions hold whether or not a formatter
    // was available to the generator.
    private static void assertGenerated(String generated, String expected) {
        assertTrue(compact(generated).contains(compact(expected)),
                () -> "missing from generated code:\n" + expected + "\ngenerated:\n" + generated);
    }

    private static String compact(String code) {
        return code.replaceAll("\\s+", "").replace(",)", ")").replace(",]", "]").replace(",}", "}");
    }
}
