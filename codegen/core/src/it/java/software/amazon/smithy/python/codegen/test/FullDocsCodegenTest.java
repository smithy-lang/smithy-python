/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

/**
 * Input members are documented where callers write them: in the Args of both clients'
 * operations and on the keys of the dictionary forms.
 */
public class FullDocsCodegenTest {

    private static final String PACKAGE = "src/docs_client";
    private static final String NAMESPACE = "example.docs#";
    // More shapes than the model stub declares in one file.
    private static final int PADDING_SHAPES = 250;

    @Test
    public void documentsInputMembersWhereCallersWriteThem(@TempDir Path tempDir) throws Exception {
        generate(loadModel(), tempDir);

        // The model is small, so the public stub declares every model itself.
        assertFalse(Files.exists(tempDir.resolve(PACKAGE + "/_private/models_0.pyi")));
        assertDocumented(tempDir);
    }

    @Test
    public void documentsInputMembersInPartitionedStubs(@TempDir Path tempDir) throws Exception {
        generate(withPadding(loadModel()), tempDir);

        var privateDirectory = tempDir.resolve(PACKAGE + "/_private");
        assertTrue(Files.exists(privateDirectory.resolve("models_0.pyi")));
        assertTrue(Files.exists(privateDirectory.resolve("models_1.pyi")));
        var partitions = new StringBuilder();
        try (var files = Files.newDirectoryStream(privateDirectory, "models_*.pyi")) {
            for (var file : files) {
                partitions.append(Files.readString(file));
            }
        }

        // The public stub now declares no model or dictionary form. It re-exports
        // them from the partitions that do, so the checks below, which start from
        // the public stub, can only find a declaration by following a re-export.
        var stub = Files.readString(tempDir.resolve(PACKAGE + "/models.pyi"));
        for (var name : List.of(
                "AssumeAccessInput",
                "AssumeAccessInputParams",
                "MigrateSessionInput",
                "MigrateSessionInputParams",
                "SessionTag",
                "SessionTagParams",
                "CredentialSourceWebToken",
                "CredentialSourceWebTokenParams",
                "CredentialSourceProfileParams",
                "UploadDocumentInputParams",
                "AsyncUploadDocumentInputParams",
                "WatchAccessInputParams")) {
            assertFalse(stub.contains("class " + name + "("), name + " is declared in the public stub");
            assertTrue(stub.contains(name + " as " + name + ","), name + " is not re-exported");
            assertTrue(partitions.toString().contains("class " + name + "("), name + " is in no partition");
        }

        // The same checks as for the small model: the padding changes no signature,
        // dictionary form or documentation.
        assertDocumented(tempDir);
    }

    private static Model loadModel() {
        var loader = FullDocsCodegenTest.class.getClassLoader();
        return Model.assembler(loader)
                .discoverModels(loader)
                .addImport(FullDocsCodegenTest.class.getResource("full-docs.smithy"))
                .assemble()
                .unwrap();
    }

    // Adds enough shapes for the model stub to be partitioned. They are empty and
    // undocumented, and are reached only through the output of AssumeAccess, so no
    // operation, input or dictionary form changes. They are all members of one
    // structure, so the model gets wider and no deeper.
    private static Model withPadding(Model model) {
        var builder = model.toBuilder();
        var padding = StructureShape.builder().id(NAMESPACE + "Padding");
        for (int i = 0; i < PADDING_SHAPES; i++) {
            var shape = StructureShape.builder().id(NAMESPACE + "Padding" + i).build();
            builder.addShape(shape);
            padding.addMember("padding" + i, shape.getId());
        }
        builder.addShape(padding.build());
        var output = model.expectShape(ShapeId.from(NAMESPACE + "AssumeAccessOutput"), StructureShape.class);
        builder.addShape(output.toBuilder().addMember("padding", ShapeId.from(NAMESPACE + "Padding")).build());
        return builder.build();
    }

    private static void generate(Model model, Path directory) {
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(directory))
                .settings(ObjectNode.builder()
                        .withMember("service", NAMESPACE + "DocsService")
                        .withMember("module", "docs_client")
                        .withMember("moduleVersion", "0.0.1")
                        .build())
                .model(model)
                .build();
        new PythonClientCodegenPlugin().execute(context);
    }

    // The checks parse the generated Python and read its decoded docstrings, which
    // is what a caller's tools show, so they are written in Python.
    private static void assertDocumented(Path directory) throws Exception {
        var script = Path.of(FullDocsCodegenTest.class.getResource("full_docs_check.py").toURI());
        var process = new ProcessBuilder("python3", script.toString(), directory.toString())
                .redirectErrorStream(true)
                .start();
        var output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertTrue(process.waitFor(60, TimeUnit.SECONDS), "the documentation checks timed out");
        assertEquals(0, process.exitValue(), output);
    }
}
