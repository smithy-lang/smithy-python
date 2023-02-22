/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import java.nio.file.Paths;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
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
import software.amazon.smithy.codegen.core.directed.GenerateIntEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateResourceDirective;
import software.amazon.smithy.codegen.core.directed.GenerateServiceDirective;
import software.amazon.smithy.codegen.core.directed.GenerateStructureDirective;
import software.amazon.smithy.codegen.core.directed.GenerateUnionDirective;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.CollectionShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.integration.ProtocolGenerator;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.EndpointProviderSection;
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
                .protocolGenerator(resolveProtocolGenerator(
                        directive.integrations(), directive.model(), directive.service(), directive.settings()))
                .build();
    }

    private ProtocolGenerator resolveProtocolGenerator(
            Collection<PythonIntegration> integrations,
            Model model,
            ServiceShape service,
            PythonSettings settings
    ) {
        // Collect all of the supported protocol generators.
        Map<ShapeId, ProtocolGenerator> generators = new HashMap<>();
        for (PythonIntegration integration : integrations) {
            for (ProtocolGenerator generator : integration.getProtocolGenerators()) {
                generators.put(generator.getProtocol(), generator);
            }
        }

        ShapeId protocolName;
        try {
            protocolName = settings.resolveServiceProtocol(model, service, generators.keySet());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find a protocol generator for " + service.getId() + ": " + e.getMessage());
            protocolName = null;
        }

        return protocolName != null ? generators.get(protocolName) : null;
    }

    @Override
    public void customizeBeforeShapeGeneration(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        generateDefaultWrapper(directive.settings(), directive.context().writerDelegator());
        generateServiceErrors(directive.settings(), directive.context().writerDelegator());
        addDefaultEndpointProvider(directive);
        new ConfigGenerator(directive.settings(), directive.context()).run();
    }

    public void addDefaultEndpointProvider(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        // Only add an endpoint provider in HTTP protocols. Some similar interface may be reasonable for
        // other application protocols, but there are still some potential http-isms in the shared interfaces
        // that we'll need to evaluate first.
        if (!directive.context().applicationProtocol().isHttpProtocol()) {
            return;
        }
        var endpointParams = CodegenUtils.getEndpointParams(directive.settings());
        var endpointResolver = CodegenUtils.getEndpointResolver(directive.settings());

        // Sections like this allow us to write a default implementation that others can overwrite later on
        // using CodeInterceptors (which is distinct from the runtime interceptor concept). A CodeInterceptor
        // is called when a matching CodeSection like this is popped, and it can modify what was generated
        // or overwrite it entirely. The advantage of typed sections like this is it allows us to pass params.
        var endpointsSection = new EndpointProviderSection(endpointResolver, endpointParams);
        var delegator = directive.context().writerDelegator();
        delegator.useFileWriter(endpointParams.getDefinitionFile(), endpointParams.getNamespace(), writer -> {
            writer.pushState(endpointsSection);
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);

            // TODO: Update these when the default implementations are moved.
            writer.getImportContainer().addImport(
                    "smithy_python._private.http", "StaticEndpointParams", "StaticEndpointParams");
            writer.getImportContainer().addImport(
                    "smithy_python._private.http", "StaticEndpointResolver", "StaticEndpointResolver");

            // We theoretically could just generate the entire code content of these,
            // but then it's a bit harder to test.
            writer.write("""
                    $L = StaticEndpointParams
                    $L = StaticEndpointResolver
                    """, endpointParams.getName(), endpointResolver.getName());

            // Popping the state will allow interceptors to provide their own implementations.
            writer.popState();
        });
    }

    @Override
    public void generateService(GenerateServiceDirective<GenerationContext, PythonSettings> directive) {
        new ClientGenerator(directive.context(), directive.service()).run();

        var protocolGenerator = directive.context().protocolGenerator();
        if (protocolGenerator == null) {
            return;
        }

        protocolGenerator.generateSharedSerializerComponents(directive.context());
        protocolGenerator.generateRequestSerializers(directive.context());

        protocolGenerator.generateSharedDeserializerComponents(directive.context());
        protocolGenerator.generateResponseDeserializers(directive.context());

        protocolGenerator.generateProtocolTests(directive.context());
    }

    private void generateDefaultWrapper(PythonSettings settings, WriterDelegator<PythonWriter> writers) {
        var wrapperClass = CodegenUtils.getDefaultWrapperClass(settings);
        writers.useFileWriter(wrapperClass.getDefinitionFile(), wrapperClass.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                    class _DEFAULT:
                        def __init__(self, wrapped: Any):
                            ""\"Wraps a value to signal it was provided by default.

                            These values will be immediately unwrapped in the associated
                            initializers so the values can be used as normal, the defaultedness
                            will then be tracked separately.
                            ""\"
                            self._wrapped = wrapped

                        @property
                        def value(self) -> Any:
                            # Prevent mutations from leaking by simply returning copies of mutable
                            # defaults. We could also just make immutable subclasses.
                            if isinstance(self._wrapped, list):
                                return list(self._wrapped)
                            if isinstance(self._wrapped, dict):
                                return dict(self._wrapped)
                            return self._wrapped

                        def __repr__(self) -> str:
                            return f"_DEFAULT({repr(self._wrapped)})"

                        def __str__(self) -> str:
                            return str(self._wrapped)
                    """);
        });

        var wrapperFunction = CodegenUtils.getDefaultWrapperFunction(settings);
        writers.useFileWriter(wrapperFunction.getDefinitionFile(), wrapperFunction.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "TypeVar");
            writer.addStdlibImport("typing", "cast");
            writer.write("""
                        _D = TypeVar("_D")


                        def _default(value: _D) -> _D:
                            ""\"Wraps a value to signal it was provided by default.

                            These values will be immediately unwrapped in the associated
                            initializers so the values can be used as normal, the defaultedness
                            will then be tracked separately.

                            We use this wrapper function for brevity, but also because many completion
                            tools will show the code of the default rather than the result, and
                            `_default(7)` is a bit more clear than `cast(int, _DEFAULT(7))`.
                            ""\"
                            return cast(_D, $T(value))
                        """, wrapperClass);
        });
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
    public void generateResource(GenerateResourceDirective<GenerationContext, PythonSettings> directive) {
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
    public void generateIntEnumShape(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        new IntEnumGenerator(directive).run();
    }

    @Override
    public void customizeBeforeIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        generateInits(directive);
        generateDictHelpers(directive);
    }

    private void generateDictHelpers(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        Iterator<Shape> shapes = new Walker(directive.model()).iterateShapes(directive.service());
        while (shapes.hasNext()) {
            Shape shape = shapes.next();
            if (shape.isListShape()) {
                generateCollectionDictHelpers(directive.context(), shape.asListShape().get());
            } else if (shape.isMapShape()) {
                generateMapDictHelpers(directive.context(), shape.asMapShape().get());
            }
        }
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
    private void generateInits(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        var directories = directive.context().writerDelegator().getWriters().keySet().stream()
                .map(Paths::get)
                .filter(path -> !path.getParent().equals(directive.fileManifest().getBaseDir()))
                .collect(Collectors.groupingBy(Path::getParent, Collectors.toSet()));
        for (var entry : directories.entrySet()) {
            var initPath = entry.getKey().resolve("__init__.py");
            if (!entry.getValue().contains(initPath)) {
                directive.fileManifest().writeFile(initPath,
                        "# Code generated by smithy-python-codegen DO NOT EDIT.\n");
            }
        }
    }

    @Override
    public void customizeAfterIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        Pattern versionPattern = Pattern.compile("Python \\d\\.(?<minor>\\d+)\\.(?<patch>\\d+)");
        FileManifest fileManifest = directive.fileManifest();
        SetupGenerator.generateSetup(directive.settings(), directive.context());

        LOGGER.info("Flushing writers in preparation for formatting and linting.");
        directive.context().writerDelegator().flushWriters();

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
        if (minorVersion < 11) {
            LOGGER.warning(format("""
                    Found incompatible python version 3.%s.%s, expected 3.11.0 or greater. \
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
