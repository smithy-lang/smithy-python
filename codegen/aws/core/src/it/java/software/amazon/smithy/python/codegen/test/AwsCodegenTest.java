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

        var client = Files.readString(tempDir.resolve("src/restjson/client.py"));
        assertInOrder(
                client,
                "config = await AsyncRESTJSONConfig.resolve()",
                "for plugin in self._client_plugins:",
                "for plugin in self._plugins:",
                "self._config = config",
                "if operation_plugins:",
                "config = deepcopy(self._config)",
                "for plugin in operation_plugins:",
                "config = self._config");
        assertFalse(client.contains("plugin(self._config)"));
        assertTrue(client.contains("retry_mode=config.retry_mode"));
        assertTrue(client.contains("max_attempts=config.max_attempts"));
        assertFalse(client.contains("getattr(config, \"retry_mode\""));
        assertFalse(client.contains("getattr(config, \"max_attempts\""));
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
