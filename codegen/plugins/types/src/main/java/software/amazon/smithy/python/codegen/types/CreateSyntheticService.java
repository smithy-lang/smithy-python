/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import java.util.HashSet;
import java.util.Set;
import java.util.logging.Logger;
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
    private static final Logger LOGGER = Logger.getLogger(CreateSyntheticService.class.getName());
    private static final String SYNTHETIC_NAMESPACE = "smithy.synthetic";
    private static final String SYNTHETIC_OPERATION_NAME = "TypesGenOperation";
    static final ShapeId SYNTHETIC_SERVICE_ID = ShapeId.fromParts(SYNTHETIC_NAMESPACE, "TypesGenService");
    private static final Set<ShapeType> GENERATED_TYPES = Set.of(
            ShapeType.STRUCTURE,
            ShapeType.UNION,
            ShapeType.ENUM,
            ShapeType.INT_ENUM);
    private static final Set<ShapeId> TRAIT_BLOCKLIST =
            Set.of(MixinTrait.ID, ProtocolDefinitionTrait.ID, TraitDefinition.ID, PrivateTrait.ID);

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
            var operationBuilder = OperationShape.builder().id(operationId);

            if (shape.hasTrait(ErrorTrait.class)) {
                operationBuilder.addError(shape.getId());
            } else if (shape.hasTrait(InputTrait.class)) {
                operationBuilder.input(shape);
            } else if (shape.hasTrait(OutputTrait.class)) {
                operationBuilder.output(shape);
            } else {
                var input = StructureShape.builder()
                        .id(ShapeId.fromParts(SYNTHETIC_NAMESPACE, operationId.getName() + "Input"))
                        .addTrait(new InputTrait())
                        .addMember("member", shape.getId())
                        .build();
                index++;
                operationBuilder.input(input);
                addedShapes.add(input);
            }

            serviceBuilder.addOperation(operationId);
            addedShapes.add(operationBuilder.build());
        }

        addedShapes.add(serviceBuilder.build());

        // First, remove all existing operations and services. We don't need them, and they'll just get in the way
        // of adding input and output shapes if we're doing that.
        model = transformer.removeShapesIf(model, shape -> shape.isOperationShape() || shape.isServiceShape());

        // Then add our new service and operation so that we can generate types.
        model = transformer.replaceShapes(model, addedShapes);

        // Ensure validation gets run so we aren't generating anything too crazy
        Model.assembler().addModel(model).assemble().validate();
        return model;
    }

    private boolean shouldGenerate(Shape shape) {
        if (!GENERATED_TYPES.contains(shape.getType()) || Prelude.isPreludeShape(shape)) {
            return false;
        }

        if (!includeInputsAndOutputs && (shape.hasTrait(InputTrait.class) || shape.hasTrait(OutputTrait.class))) {
            LOGGER.finest("""
                    Skipping generating Python type for shape `%s` because it is either an input or output shape. \
                    To generate this shape anyway, set "generateInputsAndOutputs" to true.""".formatted(shape.getId()));
            return false;
        }

        for (var blockedTrait : TRAIT_BLOCKLIST) {
            if (shape.hasTrait(blockedTrait)) {
                LOGGER.finest("Skipping generating Python type for shape `%s` because it has trait `%s`".formatted(
                        shape.getId(),
                        blockedTrait));
                return false;
            }
        }

        return true;
    }
}
