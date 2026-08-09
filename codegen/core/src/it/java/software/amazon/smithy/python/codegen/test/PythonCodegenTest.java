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

        var client = Files.readString(tempDir.resolve("src/weather/client.py"));
        assertFalse(client.contains("retry_mode="));
        assertFalse(client.contains("max_attempts="));
        assertTrue(client.contains("async def close(self) -> None:"));
        assertTrue(client.contains("{id(self._config.transport): self._config.transport}"));
    }
}
