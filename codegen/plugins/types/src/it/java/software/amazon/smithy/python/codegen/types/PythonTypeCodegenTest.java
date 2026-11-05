/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
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
    public void testCodegenWithoutService(@TempDir Path tempDir) throws IOException {
        PythonTypeCodegenPlugin plugin = new PythonTypeCodegenPlugin();
        Model model = Model.assembler(PythonTypeCodegenTest.class.getClassLoader())
                .discoverModels(PythonTypeCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("module", "types_test")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);

        // Without a selected service, describe the package by its module name rather
        // than the internal synthetic service.
        var expected = "Python types for types_test";
        String pyproject = Files.readString(tempDir.resolve("pyproject.toml"));
        String readme = Files.readString(tempDir.resolve("README.md"));
        assertAll(
                () -> assertTrue(pyproject.contains("description = \"" + expected + "\"\n"), pyproject),
                () -> assertTrue(readme.contains("\n" + expected + "\n"), readme));
    }

    @Test
    public void testEveryShapeIsGeneratedAlongsideErrors(@TempDir Path tempDir) throws IOException {
        // Error shapes get their own synthetic operation; the shapes next to them must too.
        List<String> errors = List.of("ErrorA", "ErrorB", "ErrorC", "ErrorD", "ErrorE");
        List<String> structures = List.of(
                "ShapeA",
                "ShapeB",
                "ShapeC",
                "ShapeD",
                "ShapeE",
                "ShapeF",
                "ShapeG",
                "ShapeH");
        StringBuilder source = new StringBuilder("$version: \"2.0\"\nnamespace example.errors\n");
        for (String error : errors) {
            source.append("@error(\"client\")\nstructure ").append(error).append(" { message: String }\n");
        }
        for (String structure : structures) {
            source.append("structure ").append(structure).append(" { value: String }\n");
        }
        Model model = Model.assembler()
                .addUnparsedModel("errors.smithy", source.toString())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("module", "errors_test")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();

        new PythonTypeCodegenPlugin().execute(context);

        String models = Files.readString(tempDir.resolve("src/errors_test/models.py"));
        List<String> missing = new ArrayList<>();
        errors.stream().filter(name -> !models.contains("class " + name + "(")).forEach(missing::add);
        structures.stream().filter(name -> !models.contains("class " + name + ":")).forEach(missing::add);
        assertEquals(List.of(), missing, "shapes missing from models.py");
    }

    @Test
    public void testErrorsAreGeneratedAlongsideInputsAndOutputs(@TempDir Path tempDir) throws IOException {
        // With generateInputsAndOutputs, @input and @output shapes also get synthetic operations,
        // and must not take the IDs of the errors and structures around them.
        List<String> errors = List.of("ErrorA", "ErrorB", "ErrorC", "ErrorD", "ErrorE");
        List<String> structures = List.of("ShapeA", "ShapeB", "ShapeC", "ShapeD");
        List<String> operations = List.of("OpA", "OpB", "OpC", "OpD", "OpE", "OpF");
        StringBuilder source = new StringBuilder("$version: \"2.0\"\nnamespace example.io\n");
        for (String error : errors) {
            source.append("@error(\"client\")\nstructure ").append(error).append(" { message: String }\n");
        }
        for (String structure : structures) {
            source.append("structure ").append(structure).append(" { value: String }\n");
        }
        for (String operation : operations) {
            source.append("operation ")
                    .append(operation)
                    .append(" { input := { value: String }, output := { value: String } }\n");
        }
        Model model = Model.assembler()
                .addUnparsedModel("io.smithy", source.toString())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("module", "io_test")
                                .withMember("moduleVersion", "0.0.1")
                                .withMember("generateInputsAndOutputs", true)
                                .build())
                .model(model)
                .build();

        new PythonTypeCodegenPlugin().execute(context);

        String models = Files.readString(tempDir.resolve("src/io_test/models.py"));
        List<String> missing = new ArrayList<>();
        errors.stream().filter(name -> !models.contains("class " + name + "(")).forEach(missing::add);
        structures.stream().filter(name -> !models.contains("class " + name + ":")).forEach(missing::add);
        assertEquals(List.of(), missing, "shapes missing from models.py");
    }
}
