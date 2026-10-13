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
 * Simple test that executes the Python client codegen plugin for an AWS-like service.
 */
public class AwsCodegenTest {

    @Test
    public void testCodegen(@TempDir Path tempDir) throws IOException {
        PythonClientCodegenPlugin plugin = new PythonClientCodegenPlugin();
        Model model = Model.assembler(AwsCodegenTest.class.getClassLoader())
                .discoverModels(AwsCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.aws#RestJsonService")
                                .withMember("module", "restjson")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);

        var config = Files.readString(tempDir.resolve("src/restjson/config.py"));
        assertTrue(config.contains("Overrides(AwsConfigOverrides, total=False):"));
        assertTrue(config.contains("api_key: str | None"));
        assertTrue(config.contains("@dataclass(kw_only=True, repr=False, init=False)"));
        assertTrue(config.contains("**overrides: Unpack["));
        assertTrue(config.contains(
                "interceptors: list[_ServiceInterceptor] = field(default_factory=lambda: [])"));
        assertTrue(config.contains(
                "def set_auth_scheme(self, scheme: AuthScheme[Any, Any, Any, Any]) -> None:"));
        assertTrue(config.contains("auth_schemes = dict(self.auth_schemes or {})"));
        assertTrue(config.contains("auth_schemes[scheme.scheme_id] = scheme"));
        assertTrue(config.contains("self.auth_schemes = auth_schemes"));
        assertTrue(config.contains("default_factory=lambda: AIOHTTPClient()"));
        assertFalse(config.contains("from smithy_http.aio.crt import AWSCRTHTTPClient"));

        var client = Files.readString(tempDir.resolve("src/restjson/client.py"));
        assertInOrder(
                client,
                "(AsyncClient):",
                "config = await AsyncRESTJSONConfig.resolve()",
                "for plugin in self._client_plugins:",
                "for plugin in self._plugins:",
                "await self._post_setup(config)",
                "self._config = config");
        assertTrue(client.contains("async def _post_setup(self, config:"));
        assertTrue(client.contains("for plugin in default_plugins:"));
        assertTrue(client.contains("await self._prepare_call("));
        assertTrue(client.contains("self._build_call("));
        assertFalse(client.contains("plugin(self._config)"));
        assertTrue(client.contains("retry_mode=config.retry_mode"));
        assertTrue(client.contains("max_attempts=config.max_attempts"));

        var schemas = Files.readString(tempDir.resolve("src/restjson/_private/schemas.py"));
        assertTrue(schemas.contains("aws.protocols#restJson1"));
        assertTrue(schemas.contains("smithy.api#httpApiKeyAuth"));
        assertTrue(schemas.contains("\"name\": \"weather-auth\""));
        assertTrue(schemas.contains("aws.api#service"));
        assertTrue(schemas.contains("\"sdkId\": \"REST JSON\""));
        assertTrue(schemas.contains("\"endpointPrefix\": \"rest-json-1\""));
        assertTrue(schemas.contains("\"arnNamespace\": \"rest-json\""));
        assertTrue(schemas.contains("\"cloudFormationName\": \"RestJson\""));
        assertTrue(schemas.contains("\"cloudTrailEventSource\": \"rest-json.amazonaws.com\""));
        assertTrue(schemas.contains("smithy.rules#endpointBdd"));
        assertTrue(schemas.contains("rest-json-1.{Region}.{PartitionResult#dnsSuffix}"));
    }

    private static void assertInOrder(String value, String... fragments) {
        var index = 0;
        for (String fragment : fragments) {
            index = value.indexOf(fragment, index);
            assertTrue(index >= 0, "Missing or out-of-order fragment: " + fragment);
            index += fragment.length();
        }
    }
}
