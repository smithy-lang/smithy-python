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
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

/**
 * Simple test that executes the Python client codegen plugin. Currently, this is about as much "testing" as
 * we can do, aside from the protocol tests. JUnit will set up and tear down a tempdir to house the codegen artifacts.
 */
public class PythonCodegenTest {

    @Test
    public void testCodegen(@TempDir Path tempDir) throws IOException {
        // TODO: Move this to its own package once client codegen is in its own package
        PythonClientCodegenPlugin plugin = new PythonClientCodegenPlugin();
        Model model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.weather#Weather")
                                .withMember("module", "weather")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);

        var client = Files.readString(tempDir.resolve("src/weather/aio/client.py"));
        assertTrue(client.contains("class AsyncWeather(AsyncClient[AsyncConfig]):"));
        assertTrue(client.contains("return AsyncConfig()"));
        assertFalse(client.contains("_post_setup"));
        assertTrue(client.contains("await self._invoke("));
        assertTrue(client.contains("from .. import models as _models"));
        assertTrue(client.contains("_models.GET_CITY,"));

        var config = Files.readString(tempDir.resolve("src/weather/aio/config.py"));
        assertTrue(config.contains("self.transport = transport or AIOHTTPClient()"));
        assertFalse(config.contains("self.transport = transport or AWSCRTHTTPClient()"));

        var syncClient = Files.readString(tempDir.resolve("src/weather/client.py"));
        assertTrue(syncClient.contains("class Weather(Client[Config]):"));
        assertTrue(syncClient.contains("return self._invoke("));
        // Sync operations carry the same docs as async ones.
        assertTrue(syncClient.contains("An instance of `GetCityInput`."));

        var aioInit = Files.readString(tempDir.resolve("src/weather/aio/__init__.py"));
        assertTrue(aioInit.contains("__all__ = [\"AsyncWeather\", \"AsyncConfig\"]"));
        var init = Files.readString(tempDir.resolve("src/weather/__init__.py"));
        assertTrue(init.contains("__all__ = [\"Weather\", \"Config\", \"AsyncWeather\", \"AsyncConfig\"]"));
        assertTrue(init.contains("\"AsyncWeather\": \".aio.client\""));

        // Async configs take either kind of endpoint resolver; sync ones take sync only.
        assertTrue(config.contains("endpoint_resolver: EndpointResolver | AsyncEndpointResolver"));

        var syncConfig = Files.readString(tempDir.resolve("src/weather/config.py"));
        assertTrue(syncConfig.contains("self.transport = transport or Urllib3HTTPClient()"));

        // An output that models a "responseMetadata" member gets both the SDK-reserved
        // response_metadata attribute and the escaped modeled member, so neither shadows
        // the other. Field declarations live in the typed stub (models.py builds
        // classes lazily at runtime), so the surface is asserted against models.pyi.
        var models = Files.readString(tempDir.resolve("src/weather/models.pyi"));
        assertTrue(models.contains("response_metadata: ResponseMetadata"));
        assertTrue(models.contains("response_metadata_:"));

        var runtimeModels = Files.readString(tempDir.resolve("src/weather/models.py"));
        assertTrue(runtimeModels.contains("_operation_names = ("));
        assertTrue(runtimeModels.contains("_operation_data[\"GET_CITY\"]"));
        assertTrue(runtimeModels.contains("__all__.extend(_operation_names)"));
        assertTrue(runtimeModels.contains("return globals().setdefault(name, operation)"));
        assertFalse(runtimeModels.contains("GET_CITY = APIOperation("));

        // Event streams are passed through the stream API, not model constructors.
        var typecheck = Files.readString(tempDir.resolve("tests/_typecheck.py"));
        assertFalse(typecheck.contains("stream=_"));

        var schemas = readSchemaModules(tempDir.resolve("src/weather/_private"));
        assertTrue(schemas.contains("example.weather#fakeProtocol"));
        assertTrue(schemas.contains("aws.protocols#restJson1"));
        assertTrue(schemas.contains("smithy.api#httpApiKeyAuth"));
        assertTrue(schemas.contains("\"name\": \"weather-auth\""));
        // Lowering consumes the endpoint rules; the schemas no longer carry them.
        assertFalse(schemas.contains("smithy.rules#endpointBdd"));

        var endpoints = Files.readString(tempDir.resolve("src/weather/_private/endpoints.py"));
        assertTrue(endpoints.contains("(default endpointRuleSet) endpoint is not set"));
        assertTrue(config.contains(
                "self.endpoint_resolver = endpoint_resolver or BddEndpointResolver(BDD)"));
        assertTrue(config.contains("from .._private.endpoints import BDD"));
        assertTrue(syncConfig.contains("from ._private.endpoints import BDD"));
        assertTrue(schemas.contains("smithy.api#longPoll"));
        assertTrue(schemas.contains("\"timeoutMillis\": 20000"));
    }

    @Test
    public void partitionsLargeModels(@TempDir Path tempDir) throws IOException {
        var source = new StringBuilder("""
                $version: "2"
                namespace example.large

                use aws.protocols#restJson1

                @restJson1
                service Large {
                    version: "1",
                    operations: [GetLarge]
                }

                @http(method: "POST", uri: "/", code: 200)
                operation GetLarge {
                    input: GetLargeInput,
                    output: GetLargeOutput
                }

                @input
                structure GetLargeInput {
                    root: Shape0
                }

                @output
                structure GetLargeOutput {}

                """);
        for (int i = 0; i < 250; i++) {
            source.append("structure Shape")
                    .append(i)
                    .append(" { next: Shape")
                    .append(i + 1)
                    .append(" }\n");
        }
        source.append("structure Shape250 {}\n");

        var model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .addUnparsedModel("large.smithy", source.toString())
                .assemble()
                .unwrap();
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.large#Large")
                                .withMember("module", "large")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();

        new PythonClientCodegenPlugin().execute(context);

        var schemas = Files.readString(tempDir.resolve("src/large/_private/schemas.py"));
        assertTrue(schemas.contains("__all__ = list(_PARTITIONS)  # pyright: ignore[reportUnsupportedDunderAll]"));
        assertTrue(schemas.contains("\"SHAPE0\","));
        assertTrue(schemas.contains("\"SHAPE250\","));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/schemas_0.py")));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/schemas_1.py")));

        var models = Files.readString(tempDir.resolve("src/large/models.pyi"));
        assertTrue(models.contains("from ._private.models_0 import ("));
        assertTrue(models.contains("Shape0 as Shape0,"));
        assertTrue(models.contains("Shape250 as Shape250,"));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/models_0.pyi")));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/models_1.pyi")));
    }

    @Test
    public void keepsOperationSchemasTogether(@TempDir Path tempDir) throws IOException {
        var source = new StringBuilder("""
                $version: "2"
                namespace example.affinity

                use aws.protocols#restJson1

                @restJson1
                service Affinity {
                    version: "1",
                    operations: [
                """);
        var operationSuffixes = new ArrayList<String>();
        for (int i = 0; i < 60; i++) {
            operationSuffixes.add(i < 26
                    ? Character.toString((char) ('A' + i))
                    : Character.toString((char) ('A' + (i - 26) / 26))
                            + Character.toString((char) ('A' + (i - 26) % 26)));
        }
        for (var suffix : operationSuffixes) {
            source.append("Operation").append(suffix).append(",\n");
        }
        source.append("""
                    ]
                }

                """);
        for (var suffix : operationSuffixes) {
            source.append("@http(method: \"POST\", uri: \"/")
                    .append(suffix.toLowerCase())
                    .append("\", code: 200)\n")
                    .append("operation Operation")
                    .append(suffix)
                    .append(" { input: Operation")
                    .append(suffix)
                    .append("Input, output: Operation")
                    .append(suffix)
                    .append("Output }\n")
                    .append("@input structure Operation")
                    .append(suffix)
                    .append("Input {}\n")
                    .append("@output structure Operation")
                    .append(suffix)
                    .append("Output {}\n");
        }

        var model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .addUnparsedModel("affinity.smithy", source.toString())
                .assemble()
                .unwrap();
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.affinity#Affinity")
                                .withMember("module", "affinity")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();

        new PythonClientCodegenPlugin().execute(context);

        var schemaDirectory = tempDir.resolve("src/affinity/_private");
        for (var suffix : operationSuffixes) {
            var operationName = "OPERATION_" + suffix;
            assertSchemaDeclarationsShareModule(
                    schemaDirectory,
                    operationName + ": StaticOperationSchema",
                    operationName + "_INPUT: StaticSchema",
                    operationName + "_OUTPUT: StaticSchema");
        }
    }

    private static String readSchemaModules(Path directory) throws IOException {
        var result = new StringBuilder();
        try (var files = Files.newDirectoryStream(directory, "schemas*.py")) {
            for (var file : files) {
                result.append(Files.readString(file));
            }
        }
        return result.toString();
    }

    private static void assertSchemaDeclarationsShareModule(Path directory, String... declarations) throws IOException {
        try (var files = Files.newDirectoryStream(directory, "schemas_*.py")) {
            for (var file : files) {
                var source = Files.readString(file);
                if (source.contains(declarations[0])) {
                    for (var declaration : declarations) {
                        assertTrue(source.contains(declaration));
                    }
                    return;
                }
            }
        }
        throw new AssertionError("No schema partition contained " + declarations[0]);
    }
}
