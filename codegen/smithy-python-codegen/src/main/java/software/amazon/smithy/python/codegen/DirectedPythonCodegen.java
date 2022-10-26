/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import static java.lang.String.format;

import java.nio.file.Path;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.TopologicalIndex;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.codegen.core.directed.CreateContextDirective;
import software.amazon.smithy.codegen.core.directed.CreateSymbolProviderDirective;
import software.amazon.smithy.codegen.core.directed.CustomizeDirective;
import software.amazon.smithy.codegen.core.directed.DirectedCodegen;
import software.amazon.smithy.codegen.core.directed.GenerateEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateErrorDirective;
import software.amazon.smithy.codegen.core.directed.GenerateServiceDirective;
import software.amazon.smithy.codegen.core.directed.GenerateStructureDirective;
import software.amazon.smithy.codegen.core.directed.GenerateUnionDirective;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.CollectionShape;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.SetShape;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.utils.SmithyUnstableApi;

@SmithyUnstableApi
final class DirectedPythonCodegen implements DirectedCodegen<GenerationContext, PythonSettings, PythonIntegration> {

    private static final Logger LOGGER = Logger.getLogger(DirectedPythonCodegen.class.getName());

    @Override
    public SymbolProvider createSymbolProvider(CreateSymbolProviderDirective<PythonSettings> directive) {
        return new SymbolVisitor(directive.model(), directive.settings());
    }

    @Override
    public GenerationContext createContext(CreateContextDirective<PythonSettings, PythonIntegration> directive) {
        return GenerationContext.builder()
                .model(directive.model())
                .settings(directive.settings())
                .symbolProvider(directive.symbolProvider())
                .fileManifest(directive.fileManifest())
                .writerDelegator(new PythonDelegator(
                        directive.fileManifest(), directive.symbolProvider(), directive.settings()))
                .integrations(directive.integrations())
                .build();
    }

    @Override
    public void generateService(GenerateServiceDirective<GenerationContext, PythonSettings> directive) {
        generateDefaultTimestamp(directive.model(), directive.settings(), directive.context().writerDelegator());
        generateServiceErrors(directive.settings(), directive.context().writerDelegator());
    }

    private void generateDefaultTimestamp(Model model, PythonSettings settings, WriterDelegator<PythonWriter> writers) {
        var timestamp = CodegenUtils.getDefaultTimestamp(settings);
        if (!model.getTimestampShapes().isEmpty()) {
            writers.useFileWriter(timestamp.getDefinitionFile(), timestamp.getNamespace(), writer -> {
                writer.addStdlibImport("datetime", "datetime");
                writer.write("$L = datetime(1970, 1, 1)", timestamp.getName());
            });
        }
    }

    private void generateServiceErrors(PythonSettings settings, WriterDelegator<PythonWriter> writers) {
        var serviceError = CodegenUtils.getServiceError(settings);
        writers.useFileWriter(serviceError.getDefinitionFile(), serviceError.getNamespace(), writer -> {
            // TODO: subclass a shared error
            writer.openBlock("class $L(Exception):", "", serviceError.getName(), () -> {
                writer.writeDocs("Base error for all errors in the service.");
                writer.write("pass");
            });
        });

        var apiError = CodegenUtils.getApiError(settings);
        writers.useFileWriter(apiError.getDefinitionFile(), apiError.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "Generic");
            writer.addStdlibImport("typing", "TypeVar");
            writer.write("T = TypeVar('T')");
            writer.openBlock("class $L($T, Generic[T]):", "", apiError.getName(), serviceError, () -> {
                writer.writeDocs("Base error for all api errors in the service.");
                writer.write("code: T");
                writer.openBlock("def __init__(self, message: str):", "", () -> {
                    writer.write("super().__init__(message)");
                    writer.write("self.message = message");
                });
            });

            var unknownApiError = CodegenUtils.getUnknownApiError(settings);
            writer.addStdlibImport("typing", "Literal");
            writer.openBlock("class $L($T[Literal['Unknown']]):", "", unknownApiError.getName(), apiError, () -> {
                writer.writeDocs("Error representing any unknown api errors");
                writer.write("code: Literal['Unknown'] = 'Unknown'");
            });
        });
    }

    @Override
    public void generateStructure(GenerateStructureDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            StructureGenerator generator = new StructureGenerator(
                    directive.model(),
                    directive.settings(),
                    directive.symbolProvider(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes()
            );
            generator.run();
        });
    }

    @Override
    public void generateError(GenerateErrorDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            StructureGenerator generator = new StructureGenerator(
                    directive.model(),
                    directive.settings(),
                    directive.symbolProvider(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes()
            );
            generator.run();
        });
    }

    @Override
    public void generateUnion(GenerateUnionDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            UnionGenerator generator = new UnionGenerator(
                    directive.model(),
                    directive.symbolProvider(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes()
            );
            generator.run();
        });
    }

    @Override
    public void generateEnumShape(GenerateEnumDirective<GenerationContext, PythonSettings> directive) {
        if (!directive.shape().isEnumShape()) {
            return;
        }
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            EnumGenerator generator = new EnumGenerator(
                    directive.model(),
                    directive.symbolProvider(),
                    writer,
                    directive.shape().asEnumShape().get()
            );
            generator.run();
        });
    }

    @Override
    public void customizeBeforeIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        generateDictHelpers(directive.context());
        generateInits(directive.fileManifest());
    }

    private void generateDictHelpers(GenerationContext context) {
        context.model().shapes(ListShape.class).forEach(shape -> generateCollectionDictHelpers(context, shape));
        context.model().shapes(SetShape.class).forEach(shape -> generateCollectionDictHelpers(context, shape));
        context.model().shapes(MapShape.class).forEach(shape -> generateMapDictHelpers(context, shape));
    }

    private Void generateCollectionDictHelpers(GenerationContext context, CollectionShape shape) {
        SymbolProvider symbolProvider = context.symbolProvider();
        WriterDelegator<PythonWriter> writers = context.writerDelegator();
        var optionalAsDictSymbol = symbolProvider.toSymbol(shape).getProperty("asDict", Symbol.class);
        optionalAsDictSymbol.ifPresent(asDictSymbol -> {
            writers.useFileWriter(asDictSymbol.getDefinitionFile(), asDictSymbol.getNamespace(), writer -> {
                new CollectionGenerator(context.model(), symbolProvider, writer, shape).run();
            });
        });
        return null;
    }

    public Void generateMapDictHelpers(GenerationContext context, MapShape shape) {
        SymbolProvider symbolProvider = context.symbolProvider();
        WriterDelegator<PythonWriter> writers = context.writerDelegator();
        var optionalAsDictSymbol = symbolProvider.toSymbol(shape).getProperty("asDict", Symbol.class);
        optionalAsDictSymbol.ifPresent(asDictSymbol -> {
            writers.useFileWriter(asDictSymbol.getDefinitionFile(), asDictSymbol.getNamespace(), writer -> {
                new MapGenerator(context.model(), symbolProvider, writer, shape).run();
            });
        });
        return null;
    }

    /**
     * Creates __init__.py files where not already present.
     */
    private void generateInits(FileManifest fileManifest) {
        var directories = fileManifest.getFiles().stream()
                .filter(path -> !path.getParent().equals(fileManifest.getBaseDir()))
                .collect(Collectors.groupingBy(Path::getParent, Collectors.toSet()));
        for (var entry : directories.entrySet()) {
            var initPath = entry.getKey().resolve("__init__.py");
            if (!entry.getValue().contains(initPath)) {
                fileManifest.writeFile(initPath, "# Code generated by smithy-python-codegen DO NOT EDIT.\n");
            }
        }
    }

    @Override
    public void customizeAfterIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        Pattern versionPattern = Pattern.compile("Python \\d\\.(?<minor>\\d+)\\.(?<patch>\\d+)");
        FileManifest fileManifest = directive.fileManifest();
        SetupGenerator.generateSetup(directive.settings(), directive.context().writerDelegator());

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
            LOGGER.warning(format("""
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
        formatCode(fileManifest);
        runMypy(fileManifest);
    }

    private void formatCode(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m black -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package black. Skipping formatting.");
            return;
        }
        LOGGER.info("Running code formatter on generated code");
        CodegenUtils.runCommand("python3 -m black . --exclude \"\"", fileManifest.getBaseDir());
    }

    private void runMypy(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m mypy -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package mypy. Skipping type checking.");
            return;
        }
        LOGGER.info("Running mypy on generated code");
        CodegenUtils.runCommand("python3 -m mypy .", fileManifest.getBaseDir());
    }
}
