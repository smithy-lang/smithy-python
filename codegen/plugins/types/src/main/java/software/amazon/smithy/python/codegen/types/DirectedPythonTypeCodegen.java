/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

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
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.InputTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonFormatter;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSymbolProvider;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.generators.EnumGenerator;
import software.amazon.smithy.python.codegen.generators.InitGenerator;
import software.amazon.smithy.python.codegen.generators.IntEnumGenerator;
import software.amazon.smithy.python.codegen.generators.ListGenerator;
import software.amazon.smithy.python.codegen.generators.MapGenerator;
import software.amazon.smithy.python.codegen.generators.SchemaGenerator;
import software.amazon.smithy.python.codegen.generators.ServiceErrorGenerator;
import software.amazon.smithy.python.codegen.generators.StructureGenerator;
import software.amazon.smithy.python.codegen.generators.UnionGenerator;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.writer.PythonDelegator;

final class DirectedPythonTypeCodegen
        implements DirectedCodegen<GenerationContext, PythonSettings, PythonIntegration> {
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
                .build();
    }

    @Override
    public void customizeBeforeShapeGeneration(CustomizeDirective<GenerationContext, PythonSettings> directive) {
        new ServiceErrorGenerator(directive.settings(), directive.context().writerDelegator()).run();
        SchemaGenerator.generateAll(directive.context(), directive.connectedShapes().values(), shape -> {
            if (shape.isOperationShape() || shape.isServiceShape()) {
                return false;
            }
            if (shape.isStructureShape()) {
                return shouldGenerateStructure(directive.settings(), shape);
            }
            return true;
        });
    }

    @Override
    public void generateService(GenerateServiceDirective<GenerationContext, PythonSettings> directive) {}

    @Override
    public void generateStructure(GenerateStructureDirective<GenerationContext, PythonSettings> directive) {
        // If we're only generating data shapes, there's no need to generate input or output shapes.
        if (!shouldGenerateStructure(directive.settings(), directive.shape())) {
            return;
        }

        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            StructureGenerator generator = new StructureGenerator(
                    directive.context(),
                    writer,
                    directive.shape(),
                    TopologicalIndex.of(directive.model()).getRecursiveShapes());
            generator.run();
        });
    }

    private boolean shouldGenerateStructure(PythonSettings settings, Shape shape) {
        if (shape.getId().getNamespace().equals("smithy.synthetic")) {
            return false;
        }
        return !(settings.artifactType().equals(PythonSettings.ArtifactType.TYPES)
                && (shape.hasTrait(InputTrait.class) || shape.hasTrait(OutputTrait.class)));
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
