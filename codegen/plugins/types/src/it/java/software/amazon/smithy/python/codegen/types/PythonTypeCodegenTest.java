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
        String models = generate(tempDir, errors() + structures(8), settings());

        assertEquals(List.of(), missing(models, errorNames(), structureNames(8)), "shapes missing from models.py");
    }

    @Test
    public void testInputsAndOutputsAreGeneratedWhenEnabled(@TempDir Path tempDir) throws IOException {
        // @input and @output shapes get synthetic operations too, and are generated when asked for.
        String models = generate(
                tempDir,
                errors() + structures(4) + operations(),
                settings().withMember("generateInputsAndOutputs", true));

        List<String> expected = new ArrayList<>(structureNames(4));
        expected.addAll(ioNames());
        assertEquals(List.of(), missing(models, errorNames(), expected), "shapes missing from models.py");
    }

    @Test
    public void testInputsAndOutputsAreGeneratedForServiceWhenEnabled(@TempDir Path tempDir) throws IOException {
        String service =
                "service IoService { operations: [OpA, OpB, OpC, OpD, OpE, OpF], errors: [ErrorA, ErrorB, ErrorC, ErrorD, ErrorE] }\n";
        String models = generate(
                tempDir,
                errors() + operations() + service,
                settings().withMember("service", "example.types#IoService")
                        .withMember("generateInputsAndOutputs", true));

        assertEquals(List.of(), missing(models, errorNames(), ioNames()), "shapes missing from models.py");
    }

    @Test
    public void testInputsAndOutputsAreSkippedByDefault(@TempDir Path tempDir) throws IOException {
        String models = generate(tempDir, errors() + structures(4) + operations(), settings());

        assertEquals(List.of(), missing(models, errorNames(), structureNames(4)), "shapes missing from models.py");
        List<String> generatedIo = ioNames().stream().filter(name -> models.contains("class " + name + ":")).toList();
        assertEquals(List.of(), generatedIo, "input/output shapes generated without generateInputsAndOutputs");
    }

    private static final List<String> OPERATIONS = List.of("OpA", "OpB", "OpC", "OpD", "OpE", "OpF");

    private static List<String> errorNames() {
        return List.of("ErrorA", "ErrorB", "ErrorC", "ErrorD", "ErrorE");
    }

    private static List<String> structureNames(int count) {
        return List.of("ShapeA", "ShapeB", "ShapeC", "ShapeD", "ShapeE", "ShapeF", "ShapeG", "ShapeH")
                .subList(0, count);
    }

    private static List<String> ioNames() {
        List<String> names = new ArrayList<>();
        for (String operation : OPERATIONS) {
            names.add(operation + "Input");
            names.add(operation + "Output");
        }
        return names;
    }

    private static String errors() {
        StringBuilder source = new StringBuilder();
        for (String error : errorNames()) {
            source.append("@error(\"client\")\nstructure ").append(error).append(" { message: String }\n");
        }
        return source.toString();
    }

    private static String structures(int count) {
        StringBuilder source = new StringBuilder();
        for (String structure : structureNames(count)) {
            source.append("structure ").append(structure).append(" { value: String }\n");
        }
        return source.toString();
    }

    private static String operations() {
        StringBuilder source = new StringBuilder();
        for (String operation : OPERATIONS) {
            source.append("operation ")
                    .append(operation)
                    .append(" { input := { value: String }, output := { value: String } }\n");
        }
        return source.toString();
    }

    private static ObjectNode.Builder settings() {
        return ObjectNode.builder().withMember("module", "types_test").withMember("moduleVersion", "0.0.1");
    }

    private static String generate(Path tempDir, String shapes, ObjectNode.Builder settings) throws IOException {
        Model model = Model.assembler()
                .addUnparsedModel("test.smithy", "$version: \"2.0\"\nnamespace example.types\n" + shapes)
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(settings.build())
                .model(model)
                .build();
        new PythonTypeCodegenPlugin().execute(context);
        return Files.readString(tempDir.resolve("src/types_test/models.py"));
    }

    // Errors are declared as `class Name(...)`, other structures as `class Name:`.
    private static List<String> missing(String models, List<String> errors, List<String> structures) {
        List<String> missing = new ArrayList<>();
        errors.stream().filter(name -> !models.contains("class " + name + "(")).forEach(missing::add);
        structures.stream().filter(name -> !models.contains("class " + name + ":")).forEach(missing::add);
        return missing;
    }
}
