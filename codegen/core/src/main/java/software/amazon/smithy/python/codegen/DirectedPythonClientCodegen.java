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
import software.amazon.smithy.codegen.core.directed.CreateContextDirective;
import software.amazon.smithy.codegen.core.directed.CreateSymbolProviderDirective;
import software.amazon.smithy.codegen.core.directed.CustomizeDirective;
import software.amazon.smithy.codegen.core.directed.DirectedCodegen;
import software.amazon.smithy.codegen.core.directed.GenerateEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateErrorDirective;
import software.amazon.smithy.codegen.core.directed.GenerateIntEnumDirective;
import software.amazon.smithy.codegen.core.directed.GenerateListDirective;
import software.amazon.smithy.codegen.core.directed.GenerateMapDirective;
import software.amazon.smithy.codegen.core.directed.GenerateOperationDirective;
import software.amazon.smithy.codegen.core.directed.GenerateServiceDirective;
import software.amazon.smithy.codegen.core.directed.GenerateStructureDirective;
import software.amazon.smithy.codegen.core.directed.GenerateUnionDirective;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.generators.ConfigGenerator;
import software.amazon.smithy.python.codegen.generators.ConformanceTestGenerator;
import software.amazon.smithy.python.codegen.generators.InitGenerator;
import software.amazon.smithy.python.codegen.generators.ModelModuleGenerator;
import software.amazon.smithy.python.codegen.generators.ModelStubGenerator;
import software.amazon.smithy.python.codegen.generators.OperationGenerator;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.generators.SchemaGenerator;
import software.amazon.smithy.python.codegen.generators.ServiceErrorGenerator;
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

        // Models are built on demand at runtime from the schemas; emit the thin
        // dynamic models.py once instead of eager per-shape classes, plus the typed
        // models.pyi stub for static tooling.
        var modelShapes = new java.util.ArrayList<>(directive.connectedShapes().values());
        new ModelModuleGenerator(directive.context(), modelShapes).run();
        new ModelStubGenerator(directive.context(), modelShapes).run();
        new ConformanceTestGenerator(directive.context(), modelShapes).run();

        new ConfigGenerator(directive.settings(), directive.context()).run();
        var serviceIndex = ServiceIndex.of(directive.model());
        if (directive.context().applicationProtocol().isHttpProtocol()) {
            if (!serviceIndex.getAuthSchemes(directive.service()).isEmpty()) {
                new HttpAuthGenerator(directive.context(), directive.settings()).run();
            }
        }
    }

    @Override
    public void generateService(GenerateServiceDirective<GenerationContext, PythonSettings> directive) {
        new ClientGenerator(directive.context(), directive.service()).run();

        var protocolGenerator = directive.context().protocolGenerator();
        if (protocolGenerator == null) {
            return;
        }
        protocolGenerator.generateProtocolTests(directive.context());
    }

    @Override
    public void generateOperation(GenerateOperationDirective<GenerationContext, PythonSettings> directive) {
        DirectedCodegen.super.generateOperation(directive);

        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            OperationGenerator generator = new OperationGenerator(
                    directive.context(),
                    writer,
                    directive.shape());
            generator.run();
        });
    }

    @Override
    public void generateStructure(GenerateStructureDirective<GenerationContext, PythonSettings> directive) {
        // Structures are built on demand at runtime; see ModelModuleGenerator.
    }

    @Override
    public void generateError(GenerateErrorDirective<GenerationContext, PythonSettings> directive) {
        // Errors are built on demand at runtime; see ModelModuleGenerator.
    }

    @Override
    public void generateUnion(GenerateUnionDirective<GenerationContext, PythonSettings> directive) {
        // Unions are built on demand at runtime; see ModelModuleGenerator.
    }

    @Override
    public void generateList(GenerateListDirective<GenerationContext, PythonSettings> directive) {
        // List serde is handled generically by the runtime codec; nothing to emit.
    }

    @Override
    public void generateMap(GenerateMapDirective<GenerationContext, PythonSettings> directive) {
        // Map serde is handled generically by the runtime codec; nothing to emit.
    }

    @Override
    public void generateEnumShape(GenerateEnumDirective<GenerationContext, PythonSettings> directive) {
        // Enums are built on demand at runtime; see ModelModuleGenerator.
    }

    @Override
    public void generateIntEnumShape(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        // Int enums are built on demand at runtime; see ModelModuleGenerator.
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
