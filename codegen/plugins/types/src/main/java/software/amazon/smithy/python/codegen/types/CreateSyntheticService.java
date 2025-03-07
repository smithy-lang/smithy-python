/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import java.util.HashSet;
import java.util.Set;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.loader.Prelude;
import software.amazon.smithy.model.selector.Selector;
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
import software.amazon.smithy.model.traits.PrivateTrait;
import software.amazon.smithy.model.traits.ProtocolDefinitionTrait;
import software.amazon.smithy.model.traits.TraitDefinition;
import software.amazon.smithy.model.transform.ModelTransformer;

final class CreateSyntheticService {
    private static final String SYNTHETIC_NAMESPACE = "smithy.synthetic";
    private static final String SYNTHETIC_OPERATION_NAME = "TypesGenOperation";
    static final ShapeId SYNTHETIC_SERVICE_ID = ShapeId.fromParts(SYNTHETIC_NAMESPACE, "TypesGenService");
    private static final Set<ShapeType> GENERATED_TYPES = Set.of(
            ShapeType.STRUCTURE,
            ShapeType.UNION,
            ShapeType.ENUM,
            ShapeType.INT_ENUM);

    private final Selector selector;
    private final boolean includeInputsAndOutputs;

    CreateSyntheticService(Selector selector, boolean includeInputsAndOutputs) {
        this.selector = selector;
        this.includeInputsAndOutputs = includeInputsAndOutputs;
    }

    Model transform(ModelTransformer transformer, Model model) {
        var addedShapes = new HashSet<Shape>();
        ServiceShape.Builder serviceBuilder = ServiceShape.builder()
                .id(SYNTHETIC_SERVICE_ID);

        var index = 0;
        for (Shape shape : selector.select(model)) {
            if (!shouldGenerate(shape)) {
                continue;
            }

            var operationId = ShapeId.fromParts(SYNTHETIC_NAMESPACE, SYNTHETIC_OPERATION_NAME + index);
            var inputId = ShapeId.fromParts(SYNTHETIC_NAMESPACE, operationId.getName() + "Input");
            var inputBuilder = StructureShape.builder()
                    .id(inputId)
                    .addTrait(new InputTrait());
            var operationBuilder = OperationShape.builder().id(operationId).input(inputId);
            serviceBuilder.addOperation(operationId);

            if (shape.hasTrait(ErrorTrait.class)) {
                operationBuilder.addError(shape.getId());
            } else {
                inputBuilder.addMember("member", shape.getId());
                index++;
            }
            addedShapes.add(inputBuilder.build());
            addedShapes.add(operationBuilder.build());
        }

        addedShapes.add(serviceBuilder.build());
        model = transformer.replaceShapes(model, addedShapes);

        // Ensure validation gets run so we aren't generating anything too crazy
        Model.assembler().addModel(model).assemble().validate();
        return model;
    }

    private boolean shouldGenerate(Shape shape) {
        if (!GENERATED_TYPES.contains(shape.getType())
                || shape.hasTrait(MixinTrait.class)
                || shape.hasTrait(ProtocolDefinitionTrait.class)
                || shape.hasTrait(TraitDefinition.class)
                || shape.hasTrait(PrivateTrait.class)
                || Prelude.isPreludeShape(shape)) {
            return false;
        }

        return includeInputsAndOutputs
                || (!shape.hasTrait(InputTrait.class) && !shape.hasTrait(OutputTrait.class));
    }
}
