/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.CodegenUtils.DEFAULT_TIMESTAMP;

import java.util.Set;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.EnumTrait;

/**
 * Orchestrates Python client generation.
 */
final class CodegenVisitor extends ShapeVisitor.Default<Void> {

    private static final Logger LOGGER = Logger.getLogger(CodegenVisitor.class.getName());

    private final PythonSettings settings;
    private final Model model;
    private final Model modelWithoutTraitShapes;
    private final ServiceShape service;
    private final FileManifest fileManifest;
    private final SymbolProvider symbolProvider;
    private final PythonDelegator writers;

    CodegenVisitor(PluginContext context) {
        settings = PythonSettings.from(context.getSettings());
        model = context.getModel();
        modelWithoutTraitShapes = context.getModelWithoutTraitShapes();
        service = settings.getService(model);
        fileManifest = context.getFileManifest();
        LOGGER.info(() -> "Generating Python client for service " + service.getId());

        symbolProvider = PythonCodegenPlugin.createSymbolProvider(model);
        writers = new PythonDelegator(settings, model, fileManifest, symbolProvider);
    }

    void execute() {
        // Generate models that are connected to the service being generated.
        LOGGER.fine("Walking shapes from " + service.getId() + " to find shapes to generate");
        Set<Shape> serviceShapes = new Walker(modelWithoutTraitShapes).walkShapes(service);

        generateDefaultTimestamp(serviceShapes);

        for (Shape shape : serviceShapes) {
            shape.accept(this);
        }

        LOGGER.fine("Flushing python writers");
        writers.flushWriters();
        postProcess();
    }

    private void postProcess() {
        Pattern versionPattern = Pattern.compile("Python \\d\\.(?<minor>\\d+)\\.(?<patch>\\d+)");

        String output;
        try {
            LOGGER.info("Attempting to discover python version");
            output = CodegenUtils.runCommand("python3 --version", fileManifest.getBaseDir()).strip();
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find python on the path. Skipping formatting and type checking.");
            return;
        }
        var matcher = versionPattern.matcher(output);
        if (!matcher.find()) {
            LOGGER.warning("Unable to parse python version string. Skipping formatting and type checking.");
        }
        int minorVersion = Integer.parseInt(matcher.group("minor"));
        if (minorVersion < 9) {
            LOGGER.warning(String.format("""
                    Found incompatible python version 3.%s.%s, expected 3.9.0 or greater. \
                    Skipping formatting and type checking.""",
                    matcher.group("minor"), matcher.group("patch")));
            return;
        }
        formatCode();
        runMypy();
    }

    private void formatCode() {
        try {
            CodegenUtils.runCommand("python3 -m black -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package black. Skipping formatting.");
            return;
        }
        LOGGER.info("Running code formatter on generated code");
        CodegenUtils.runCommand("python3 -m black . --exclude \"\"", fileManifest.getBaseDir());
    }

    private void runMypy() {
        try {
            CodegenUtils.runCommand("python3 -m mypy -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package mypy. Skipping type checking.");
            return;
        }
        LOGGER.info("Running mypy on generated code");
        CodegenUtils.runCommand("python3 -m mypy .", fileManifest.getBaseDir());
    }

    private void generateDefaultTimestamp(Set<Shape> shapes) {
        if (containsTimestampShapes(shapes)) {
            writers.useFileWriter(DEFAULT_TIMESTAMP.getDefinitionFile(), DEFAULT_TIMESTAMP.getNamespace(), writer -> {
                writer.addStdlibImport("datetime", "datetime", "datetime");
                writer.write("$L = datetime(1970, 1, 1)", DEFAULT_TIMESTAMP.getName());
            });
        }
    }

    private boolean containsTimestampShapes(Set<Shape> shapes) {
        for (Shape shape : shapes) {
            if (shape.isTimestampShape()) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected Void getDefault(Shape shape) {
        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        if (shape.hasTrait(EnumTrait.class)) {
            writers.useShapeWriter(shape, writer -> new EnumGenerator(model, symbolProvider, writer, shape).run());
        }
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        writers.useShapeWriter(shape, writer -> new StructureGenerator(model, symbolProvider, writer, shape).run());
        return null;
    }
}
