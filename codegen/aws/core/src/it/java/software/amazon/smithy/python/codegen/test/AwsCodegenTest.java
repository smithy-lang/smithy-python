/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertTrue;

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
 * Simple test that executes the Python client codegen plugin for an AWS-like service
 * and validates that MkDocs documentation files are generated.
 */
public class AwsCodegenTest {

    @Test
    public void testCodegen(@TempDir Path tempDir) {
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

        // Verify MkDocs documentation files are generated for AWS services
        Path docsDir = tempDir.resolve("docs");
        assertTrue(Files.exists(docsDir), "docs directory should be created");

        Path indexFile = docsDir.resolve("index.md");
        assertTrue(Files.exists(indexFile), "index.md should be generated for AWS services");

        Path operationsDir = docsDir.resolve("operations");
        assertTrue(Files.exists(operationsDir), "operations directory should be created");

        // Verify at least one operation file exists
        Path basicOperationFile = operationsDir.resolve("basic_operation.md");
        assertTrue(Files.exists(basicOperationFile), "basic_operation.md should be generated");
    }

}
