/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import java.util.Collection;
import java.util.Set;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.build.SmithyBuildPlugin;
import software.amazon.smithy.codegen.core.directed.CodegenDirector;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.loader.Prelude;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.model.traits.InputTrait;
import software.amazon.smithy.model.traits.MixinTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.model.transform.ModelTransformer;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

public final class PythonTypeCodegenPlugin implements SmithyBuildPlugin {
    private static final String SYNTHETIC_NAMESPACE = "smithy.synthetic";
    private static final ShapeId SYNTHETIC_SERVICE_ID = ShapeId.fromParts(SYNTHETIC_NAMESPACE, "TypesGenService");
    private static final ShapeId SYNTHETIC_OPERATION_ID = ShapeId.fromParts(SYNTHETIC_NAMESPACE, "TypesGenOperation");
    private static final ShapeId SYNTHETIC_INPUT_ID = ShapeId.fromParts(SYNTHETIC_NAMESPACE, "TypesGenOperationInput");
    private static final Set<ShapeType> GENERATED_TYPES = Set.of(
            ShapeType.STRUCTURE,
            ShapeType.UNION,
            ShapeType.ENUM,
            ShapeType.INT_ENUM);

    @Override
    public String getName() {
        return "python-type-codegen";
    }

    @Override
    public void execute(PluginContext context) {
        CodegenDirector<PythonWriter, PythonIntegration, GenerationContext, PythonSettings> runner =
                new CodegenDirector<>();

        var typeSettings = PythonTypeCodegenSettings.fromNode(context.getSettings());
        var service = typeSettings.service().orElse(SYNTHETIC_SERVICE_ID);
        var pythonSettings = typeSettings.toPythonSettings(service);

        var model = context.getModel();
        if (typeSettings.service().isEmpty()) {
            model = addSyntheticService(model, typeSettings.selector().select(model));
        }

        runner.settings(pythonSettings);
        runner.directedCodegen(new DirectedPythonTypeCodegen());
        runner.fileManifest(context.getFileManifest());
        runner.service(pythonSettings.service());
        runner.model(model);
        runner.integrationClass(PythonIntegration.class);
        runner.performDefaultCodegenTransforms();
        runner.run();
    }

    private Model addSyntheticService(Model model, Collection<Shape> shapes) {
        StructureShape.Builder inputBuilder = StructureShape.builder()
                .id(SYNTHETIC_INPUT_ID)
                .addTrait(new InputTrait());

        OperationShape.Builder operationBuilder = OperationShape.builder()
                .id(SYNTHETIC_OPERATION_ID)
                .input(SYNTHETIC_INPUT_ID);

        var index = 0;
        for (Shape shape : shapes) {
            if (!GENERATED_TYPES.contains(shape.getType())
                    || shape.hasTrait(InputTrait.class)
                    || shape.hasTrait(OutputTrait.class)
                    || shape.hasTrait(MixinTrait.class)
                    || Prelude.isPreludeShape(shape)) {
                continue;
            }

            if (shape.hasTrait(ErrorTrait.class)) {
                operationBuilder.addError(shape.getId());
            } else {
                inputBuilder.addMember("member" + index, shape.getId());
                index++;
            }
        }

        ServiceShape service = ServiceShape.builder()
                .id(SYNTHETIC_SERVICE_ID)
                .addOperation(SYNTHETIC_OPERATION_ID)
                .build();

        ModelTransformer transformer = ModelTransformer.create();
        return transformer.replaceShapes(model, Set.of(inputBuilder.build(), operationBuilder.build(), service));
    }
}
