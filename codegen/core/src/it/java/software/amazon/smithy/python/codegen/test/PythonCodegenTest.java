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

        var schemas = Files.readString(tempDir.resolve("src/weather/_private/schemas.py"));
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
}
