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

        var config = Files.readString(tempDir.resolve("src/restjson/aio/config.py"));
        assertTrue(config.contains("Overrides(AsyncAwsConfigOverrides, total=False):"));
        assertTrue(config.contains("api_key: str | None"));
        assertTrue(config.contains("@dataclass(kw_only=True, repr=False, init=False)"));
        assertTrue(config.contains("**overrides: Unpack["));
        assertTrue(config.contains(
                "interceptors: list[_ServiceInterceptor] = field(default_factory=lambda: [])"));
        assertTrue(config.contains(
                "def set_auth_scheme(self, scheme: AsyncAuthScheme[Any, Any, Any, Any]) -> None:"));
        assertTrue(config.contains("auth_schemes = dict(self.auth_schemes or {})"));
        assertTrue(config.contains("auth_schemes[scheme.scheme_id] = scheme"));
        assertTrue(config.contains("self.auth_schemes = auth_schemes"));
        assertTrue(config.contains("default_factory=lambda: AIOHTTPClient()"));
        assertFalse(config.contains("from smithy_http.aio.crt import AWSCRTHTTPClient"));

        var client = Files.readString(tempDir.resolve("src/restjson/aio/client.py"));
        assertInOrder(
                client,
                "(AsyncClient[AsyncRESTJSONConfig]):",
                "_client_plugins = (",
                "await self._invoke(",
                "async def _new_config(self) -> AsyncRESTJSONConfig:",
                "return await AsyncRESTJSONConfig.resolve()");
        assertFalse(client.contains("def __init__("));
        assertFalse(client.contains("def _ensure_setup("));
        assertFalse(client.contains("def _prepare_call["));

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
        // Lowering consumes the endpoint rules; the schemas no longer carry them.
        assertFalse(schemas.contains("smithy.rules#endpointBdd"));

        var endpoints = Files.readString(tempDir.resolve("src/restjson/_private/endpoints.py"));
        assertTrue(endpoints.contains("\"https://rest-json-1.{Region}.{PartitionResult#dnsSuffix}\""));
        // Formatting may wrap the call, so match its parts.
        assertTrue(config.contains("BddEndpointResolver("));
        assertTrue(config.contains("BDD, extensions=[AWS_RULES_EXTENSION]"));
        assertTrue(config.contains("from .._private.endpoints import BDD"));
        assertTrue(config.contains("from smithy_aws_core.endpoints import AWS_RULES_EXTENSION"));
        // The default rules declare the FIPS and dual-stack built-ins, so the config gets
        // their fields; they don't declare the account ID endpoint mode.
        assertTrue(config.contains("    use_fips_endpoint: bool | None\n"));
        assertTrue(config.contains("    use_dualstack_endpoint: bool | None\n"));
        assertTrue(config.contains("use_fips_endpoint: bool | None = None"));
        assertTrue(config.contains("use_dualstack_endpoint: bool | None = None"));
        assertInOrder(config,
                "\"use_fips_endpoint\": FieldSpec(",
                "default=None,",
                "resolver=resolve_use_fips_endpoint_program");
        assertInOrder(config,
                "\"use_dualstack_endpoint\": FieldSpec(",
                "default=None,",
                "resolver=resolve_use_dualstack_endpoint_program");
        assertFalse(config.contains("account_id_endpoint_mode"));
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
