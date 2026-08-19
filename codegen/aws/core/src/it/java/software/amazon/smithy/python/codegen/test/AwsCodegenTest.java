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

        var client = Files.readString(tempDir.resolve("src/restjson/client.py"));
        var resolveConfig = "config = await AsyncRESTJSONConfig.resolve()";
        var applyServicePlugins = "for plugin in self._client_plugins:";
        var applyConfiguredPlugins = "for plugin in self._plugins:";
        var publishConfig = "self._config = config";
        var copyOperationConfig = "config = deepcopy(self._config)";
        var applyOperationPlugins = "for plugin in operation_plugins:";

        var resolveConfigIndex = client.indexOf(resolveConfig);
        var applyServicePluginsIndex = client.indexOf(applyServicePlugins);
        var applyConfiguredPluginsIndex = client.indexOf(applyConfiguredPlugins);
        var publishConfigIndex = client.indexOf(publishConfig, applyConfiguredPluginsIndex);
        var copyOperationConfigIndex = client.indexOf(copyOperationConfig, publishConfigIndex);
        var applyOperationPluginsIndex = client.indexOf(applyOperationPlugins, copyOperationConfigIndex);

        assertTrue(resolveConfigIndex >= 0);
        assertTrue(resolveConfigIndex < applyServicePluginsIndex);
        assertTrue(applyServicePluginsIndex < applyConfiguredPluginsIndex);
        assertTrue(applyConfiguredPluginsIndex < publishConfigIndex);
        assertTrue(publishConfigIndex < copyOperationConfigIndex);
        assertTrue(copyOperationConfigIndex < applyOperationPluginsIndex);
        assertFalse(client.contains("plugin(self._config)"));
        assertTrue(client.contains("retry_mode=config.retry_mode"));
        assertTrue(client.contains("max_attempts=config.max_attempts"));
        assertFalse(client.contains("getattr(config, \"retry_mode\""));
        assertFalse(client.contains("getattr(config, \"max_attempts\""));
    }

}
