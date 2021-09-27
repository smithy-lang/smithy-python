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

import static software.amazon.smithy.python.codegen.CodegenUtils.API_ERROR;
import static software.amazon.smithy.python.codegen.CodegenUtils.DEFAULT_TIMESTAMP;
import static software.amazon.smithy.python.codegen.CodegenUtils.SERVICE_ERROR;
import static software.amazon.smithy.python.codegen.CodegenUtils.UNKNOWN_API_ERROR;

import java.util.Collection;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.TopologicalIndex;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.EnumTrait;

/**
 * Orchestrates Python client generation.
 */
final class CodegenVisitor extends ShapeVisitor.Default<Void> {

    private static final Logger LOGGER = Logger.getLogger(CodegenVisitor.class.getName());

    /**
     * A mapping of static resource files to copy over to a new filename.
     */
    private static final Map<String, String> STATIC_FILE_COPIES = Map.of(
            "setup.cfg", "setup.cfg"
    );

    private final PythonSettings settings;
    private final Model model;
    private final Model modelWithoutTraitShapes;
    private final ServiceShape service;
    private final FileManifest fileManifest;
    private final SymbolProvider symbolProvider;
    private final PythonDelegator writers;
    private Set<Shape> recursiveShapes;

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
        // Write shared / static content.
        STATIC_FILE_COPIES.forEach((from, to) -> {
            LOGGER.fine(() -> "Writing contents of `" + from + "` to `" + to + "`");
            fileManifest.writeFile(from, getClass(), to);
        });

        // Generate models that are connected to the service being generated.
        LOGGER.fine("Walking shapes from " + service.getId() + " to find shapes to generate");
        Collection<Shape> shapeSet = new Walker(modelWithoutTraitShapes).walkShapes(service);
        Model prunedModel = Model.builder().addShapes(shapeSet).build();

        generateDefaultTimestamp(prunedModel);
        generateServiceErrors();
        UnionGenerator.generateTypeVar(prunedModel, writers);

        // Sort shapes in a reverse topological order so that we can reduce the
        // number of necessary forward references.
        var topologicalIndex = TopologicalIndex.of(prunedModel);
        recursiveShapes = topologicalIndex.getRecursiveShapes();
        for (Shape shape : topologicalIndex.getOrderedShapes()) {
            shape.accept(this);
        }
        for (Shape shape : topologicalIndex.getRecursiveShapes()) {
            shape.accept(this);
        }
        LOGGER.fine("Flushing python writers");
        writers.flushWriters();
        postProcess();
    }

    private void generateServiceErrors() {
        writers.useFileWriter(SERVICE_ERROR.getDefinitionFile(), SERVICE_ERROR.getNamespace(), writer -> {
            // TODO: subclass a shared error
            writer.openBlock("class $L(Exception):", "", SERVICE_ERROR.getName(), () -> {
                writer.openDocComment(() -> {
                    writer.write("Base error for all errors in the service.");
                });
                writer.write("pass");
            });
        });

        writers.useFileWriter(API_ERROR.getDefinitionFile(), API_ERROR.getNamespace(), writer -> {
            writer.addStdlibImport("Generic", "Generic", "typing");
            writer.addStdlibImport("TypeVar", "TypeVar", "typing");
            writer.write("T = TypeVar('T')");
            writer.openBlock("class $L($T, Generic[T]):", "", API_ERROR.getName(), SERVICE_ERROR, () -> {
                writer.openDocComment(() -> {
                    writer.write("Base error for all api errors in the service.");
                });
                writer.write("code: T");
                writer.openBlock("def __init__(self, message: str):", "", () -> {
                    writer.write("super().__init__(message)");
                    writer.write("self.message = message");
                });
            });

            writer.addStdlibImport("Literal", "Literal", "typing");
            writer.openBlock("class $L($T[Literal['Unknown']]):", "", UNKNOWN_API_ERROR.getName(), API_ERROR, () -> {
                writer.openDocComment(() -> writer.write("Error representing any unknown api errors"));
                writer.write("code: Literal['Unknown'] = 'Unknown'");
            });
        });


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
        LOGGER.info("Verifying python files");
        for (var file : fileManifest.getFiles()) {
            var fileName = file.getFileName();
            if (fileName == null || !fileName.endsWith(".py")) {
                continue;
            }
            CodegenUtils.runCommand("python3 " + file, fileManifest.getBaseDir());
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

    private void generateDefaultTimestamp(Model model) {
        if (!model.getTimestampShapes().isEmpty()) {
            writers.useFileWriter(DEFAULT_TIMESTAMP.getDefinitionFile(), DEFAULT_TIMESTAMP.getNamespace(), writer -> {
                writer.addStdlibImport("datetime", "datetime", "datetime");
                writer.write("$L = datetime(1970, 1, 1)", DEFAULT_TIMESTAMP.getName());
            });
        }
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
        writers.useShapeWriter(shape, writer -> new StructureGenerator(
                model, symbolProvider, writer, shape, recursiveShapes).run());
        return null;
    }

    @Override
    public Void unionShape(UnionShape shape) {
        writers.useShapeWriter(shape, writer -> new UnionGenerator(
                model, symbolProvider, writer, shape, recursiveShapes).run());
        return null;
    }
}
