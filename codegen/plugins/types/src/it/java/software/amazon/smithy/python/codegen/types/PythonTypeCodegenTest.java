/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;

/**
 * Simple test that executes the Python type codegen plugin. Currently, this is about as much "testing" as
 * we can do, aside from the protocol tests. JUnit will set up and tear down a tempdir to house the codegen artifacts.
 */
public class PythonTypeCodegenTest {

    @Test
    public void testCodegen(@TempDir Path tempDir) {
        PythonTypeCodegenPlugin plugin = new PythonTypeCodegenPlugin();
        Model model = Model.assembler(PythonTypeCodegenTest.class.getClassLoader())
                .discoverModels(PythonTypeCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.weather#Weather")
                                .withMember("module", "types_test")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);
    }

    @Test
    public void testCodegenWithoutService(@TempDir Path tempDir) {
        PythonTypeCodegenPlugin plugin = new PythonTypeCodegenPlugin();
        Model model = Model.assembler(PythonTypeCodegenTest.class.getClassLoader())
                .discoverModels(PythonTypeCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("selector", """
                                        :test([id|namespace = 'example.weather'],
                                              [id|namespace = 'example.weather.nested'],
                                              [id|namespace = 'example.weather.nested.more'])
                                        """)
                                .withMember("module", "types_test")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);
    }
}
