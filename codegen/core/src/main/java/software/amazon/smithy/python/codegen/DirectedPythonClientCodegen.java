/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.TopologicalIndex;
import software.amazon.smithy.codegen.core.directed.CreateContextDirective;
import software.amazon.smithy.codegen.core.directed.CreateSymbolProviderDirective;
import software.amazon.smithy.codegen.core.directed.CustomizeDirective;
import software.amazon.smithy.codegen.core.directed.DirectedCodegen;
import software.amazon.smithy.codegen.core.directed.GenerateEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateErrorDirective;
import software.amazon.smithy.codegen.core.directed.GenerateIntEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateListDirective;
import software.amazon.smithy.codegen.core.directed.GenerateMapDirective;
import software.amazon.smithy.codegen.core.directed.GenerateServiceDirective;
import software.amazon.smithy.codegen.core.directed.GenerateStructureDirective;
import software.amazon.smithy.codegen.core.directed.GenerateUnionDirective;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.generators.ConfigGenerator;
import software.amazon.smithy.python.codegen.generators.EndpointsGenerator;
import software.amazon.smithy.python.codegen.generators.EnumGenerator;
import software.amazon.smithy.python.codegen.generators.InitGenerator;
import software.amazon.smithy.python.codegen.generators.IntEnumGenerator;
import software.amazon.smithy.python.codegen.generators.ListGenerator;
import software.amazon.smithy.python.codegen.generators.MapGenerator;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.generators.SchemaGenerator;
import software.amazon.smithy.python.codegen.generators.ServiceErrorGenerator;
import software.amazon.smithy.python.codegen.generators.StructureGenerator;
import software.amazon.smithy.python.codegen.generators.UnionGenerator;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.writer.PythonDelegator;
import software.amazon.smithy.utils.SmithyUnstableApi;

@SmithyUnstableApi
final class DirectedPythonClientCodegen
        implements DirectedCodegen<GenerationContext, PythonSettings, PythonIntegration> {

    private static final Logger LOGGER = Logger.getLogger(DirectedPythonClientCodegen.class.getName());

    @Override
    public SymbolProvider createSymbolProvider(CreateSymbolProviderDirective<PythonSettings> directive) {
        return new PythonSymbolProvider(directive.model(), directive.settings());
    }

    @Override
    public GenerationContext createContext(CreateContextDirective<PythonSettings, PythonIntegration> directive) {
        return GenerationContext.builder()
                .model(directive.model())
                .settings(directive.settings())
                .symbolProvider(directive.symbolProvider())
                .fileManifest(directive.fileManifest())
                .writerDelegator(new PythonDelegator(
                        directive.fileManifest(),
                        directive.symbolProvider(),
                        directive.settings()))
                .integrations(directive.integrations())
                .protocolGenerator(resolveProtocolGenerator(
                        directive.integrations(),
                        directive.model(),
                        directive.service()))
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
        new ServiceErrorGenerator(directive.settings(), directive.context().writerDelegator()).run();
        SchemaGenerator.generateAll(directive.context(), directive.connectedShapes().values());

        new ConfigGenerator(directive.settings(), directive.context()).run();
        var serviceIndex = ServiceIndex.of(directive.model());
        if (directive.context().applicationProtocol().isHttpProtocol()) {
            if (!serviceIndex.getAuthSchemes(directive.service()).isEmpty()) {
                new HttpAuthGenerator(directive.context(), directive.settings()).run();
            }
            new EndpointsGenerator(directive.context(), directive.settings()).run();
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

    @Override
    public void generateStructure(GenerateStructureDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            StructureGenerator generator = new StructureGenerator(
                    directive.context(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes());
            generator.run();
        });
    }

    @Override
    public void generateError(GenerateErrorDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            StructureGenerator generator = new StructureGenerator(
                    directive.context(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes());
            generator.run();
        });
    }

    @Override
    public void generateUnion(GenerateUnionDirective<GenerationContext, PythonSettings> directive) {
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            UnionGenerator generator = new UnionGenerator(
                    directive.context(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes());
            generator.run();
        });
    }

    @Override
    public void generateList(GenerateListDirective<GenerationContext, PythonSettings> directive) {
        var serSymbol = directive.context()
                .symbolProvider()
                .toSymbol(directive.shape())
                .expectProperty(SymbolProperties.SERIALIZER);
        var delegator = directive.context().writerDelegator();
        delegator.useFileWriter(serSymbol.getDefinitionFile(), serSymbol.getNamespace(), writer -> {
            new ListGenerator(directive.context(), writer, directive.shape()).run();
        });
    }

    @Override
    public void generateMap(GenerateMapDirective<GenerationContext, PythonSettings> directive) {
        var serSymbol = directive.context()
                .symbolProvider()
                .toSymbol(directive.shape())
                .expectProperty(SymbolProperties.SERIALIZER);
        var delegator = directive.context().writerDelegator();
        delegator.useFileWriter(serSymbol.getDefinitionFile(), serSymbol.getNamespace(), writer -> {
            new MapGenerator(directive.context(), writer, directive.shape()).run();
        });
    }

    @Override
    public void generateEnumShape(GenerateEnumDirective<GenerationContext, PythonSettings> directive) {
        if (!directive.shape().isEnumShape()) {
            return;
        }
        new EnumGenerator(directive.context(), directive.shape().asEnumShape().get()).run();
    }

    @Override
    public void generateIntEnumShape(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        new IntEnumGenerator(directive).run();
    }

    @Override
    public void customizeBeforeIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        new InitGenerator(directive.context()).run();
        PythonIntegration.generatePluginFiles(directive.context());
    }

    @Override
    public void customizeAfterIntegrations(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        new PythonFormatter(directive.context()).run();
    }
}
