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
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.CodegenException;
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
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.integration.ProtocolGenerator;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.utils.SmithyUnstableApi;

@SmithyUnstableApi
final class DirectedPythonCodegen implements DirectedCodegen<GenerationContext, PythonSettings, PythonIntegration> {

    private static final Logger LOGGER = Logger.getLogger(DirectedPythonCodegen.class.getName());
    private static final int PYTHON_MINOR_VERSION = 12; // 3.12

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
                        directive.integrations(), directive.model(), directive.service()))
                .build();
    }

    private ProtocolGenerator resolveProtocolGenerator(
            Collection<PythonIntegration> integrations,
            Model model,
            ServiceShape service
    ) {
        // Collect all the supported protocol generators.
        Map<ShapeId, ProtocolGenerator> generators = new HashMap<>();
        for (PythonIntegration integration : integrations) {
            for (ProtocolGenerator generator : integration.getProtocolGenerators()) {
                generators.put(generator.getProtocol(), generator);
            }
        }

        ServiceIndex serviceIndex = ServiceIndex.of(model);
        Set<ShapeId> resolvedProtocols = serviceIndex.getProtocols(service).keySet();
        Optional<ShapeId> protocol = resolvedProtocols.stream()
                .filter(generators::containsKey)
                .findFirst();

        if (protocol.isPresent()) {
            return generators.get(protocol.get());
        }

        LOGGER.warning("Unable to find a protocol generator for " + service.getId());
        return null;
    }

    @Override
    public void customizeBeforeShapeGeneration(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        generateServiceErrors(directive.settings(), directive.context().writerDelegator());
        new ConfigGenerator(directive.settings(), directive.context()).run();

        var serviceIndex = ServiceIndex.of(directive.model());
        if (directive.context().applicationProtocol().isHttpProtocol()
                && !serviceIndex.getAuthSchemes(directive.service()).isEmpty()) {
            new HttpAuthGenerator(directive.context(), directive.settings()).run();
        }
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

    private void generateServiceErrors(PythonSettings settings, WriterDelegator<PythonWriter> writers) {
        var serviceError = CodegenUtils.getServiceError(settings);
        writers.useFileWriter(serviceError.getDefinitionFile(), serviceError.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addImport("smithy_core.exceptions", "SmithyException");
            writer.write("""
                    class $L(SmithyException):
                        ""\"Base error for all errors in the service.""\"
                        pass
                    """, serviceError.getName());
        });

        var apiError = CodegenUtils.getApiError(settings);
        writers.useFileWriter(apiError.getDefinitionFile(), apiError.getNamespace(), writer -> {
            writer.addStdlibImports("typing", Set.of("Literal", "ClassVar"));
            var unknownApiError = CodegenUtils.getUnknownApiError(settings);

            writer.write("""
                    @dataclass
                    class $1L($2T):
                        ""\"Base error for all API errors in the service.""\"
                        code: ClassVar[str]
                        fault: ClassVar[Literal["client", "server"]]

                        message: str

                        def __post_init__(self) -> None:
                            super().__init__(self.message)


                    @dataclass
                    class $3L($1L):
                        ""\"Error representing any unknown api errors""\"
                        code: ClassVar[str] = 'Unknown'
                        fault: ClassVar[Literal["client", "server"]] = "client"
                    """, apiError.getName(), serviceError, unknownApiError.getName());
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
        if (minorVersion < PYTHON_MINOR_VERSION) {
            LOGGER.warning(String.format("""
                    Found incompatible python version 3.%s.%s, expected 3.12.0 or greater. \
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
        format(fileManifest);
        check(fileManifest);
    }

    private void format(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m black -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package black. Skipping formatting.");
            return;
        }
        LOGGER.info("Running code formatter on generated code");
        CodegenUtils.runCommand("python3 -m black . --exclude \"\"", fileManifest.getBaseDir());
    }

    private void check(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m pyright -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the pyright package. Skipping type checking.");
            return;
        }
        LOGGER.info("Running mypy on generated code");
        CodegenUtils.runCommand("python3 -m pyright .", fileManifest.getBaseDir());
    }
}
