/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ToShapeId;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.IdempotencyTokenTrait;
import software.amazon.smithy.model.traits.RequiredTrait;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Describes how operation inputs are written by callers: as keyword arguments whose
 * nested structures and unions are either generated models or dictionaries.
 *
 * <p>Every structure and union reachable from an operation's input has a
 * {@code TypedDict} form, named with a {@code Params} suffix, that the model stub
 * declares and client method signatures refer to. This class decides which shapes
 * have one, what it is called, and how a member's accepted type is spelled, so the
 * stub and the client cannot disagree.
 *
 * <p>An operation input with a streaming blob member has two forms, because the two
 * clients accept different bodies. The plain form takes the bodies a sync client
 * accepts, which an async client accepts too, so it can be unpacked into either. The
 * form with an {@code Async} prefix also takes async streams, and only the async
 * client accepts it. This follows the runtime's naming of mode-specific types.
 */
@SmithyInternalApi
public final class InputParams {

    private static final String SUFFIX = "Params";
    private static final String ASYNC_PREFIX = "Async";

    private static final Symbol SEQUENCE = Symbol.builder()
            .name("Sequence")
            .namespace("collections.abc", ".")
            .putProperty(SymbolProperties.STDLIB, true)
            .build();
    private static final Symbol MAPPING = Symbol.builder()
            .name("Mapping")
            .namespace("collections.abc", ".")
            .putProperty(SymbolProperties.STDLIB, true)
            .build();

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final OperationIndex operationIndex;
    private final String modelsNamespace;
    // Structures and unions reachable from an operation input, and union members.
    private final Map<ShapeId, String> names = new HashMap<>();
    // Operation inputs with a streaming blob member.
    private final Map<ShapeId, String> asyncNames = new HashMap<>();

    public InputParams(GenerationContext context) {
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.operationIndex = OperationIndex.of(model);
        this.modelsNamespace = context.settings().moduleName() + ".models";

        var service = context.settings().service(model);
        var reachable = new LinkedHashSet<Shape>();
        var streaming = new TreeSet<Shape>();
        for (var operation : TopDownIndex.of(model).getContainedOperations(service)) {
            var input = model.expectShape(operation.getInputShape());
            collect(input, reachable);
            if (input.members().stream().anyMatch(this::isStreamingBlob)) {
                streaming.add(input);
            }
        }

        // Every class the models module defines. A dictionary form whose plain name
        // is taken gets underscores before the suffix until it is free.
        //
        // CAUTION: smithy_core._dynamic_models.ModelRegistry resolves these names at
        // runtime without being told them: it takes the suffix off a name, then
        // underscores one at a time until a modeled name is left. A shape's own name
        // may end in underscores, so it does not strip them all.
        var taken = new HashSet<String>();
        taken.add(CodegenUtils.getServiceError(context.settings()).getName());
        for (var shape : new Walker(model).walkShapes(service)) {
            if (shape.isStructureShape()) {
                taken.add(symbolProvider.toSymbol(shape).getName());
            } else if (shape.isUnionShape()) {
                var symbol = symbolProvider.toSymbol(shape);
                taken.add(symbol.getName());
                taken.add(symbol.expectProperty(SymbolProperties.UNION_UNKNOWN).getName());
                for (var member : shape.members()) {
                    taken.add(symbolProvider.toSymbol(member).getName());
                }
            } else if (shape.isEnumShape() || shape.isIntEnumShape()) {
                taken.add(symbolProvider.toSymbol(shape).expectProperty(SymbolProperties.ENUM_SYMBOL).getName());
            }
        }

        // Sorted so the names don't depend on traversal order.
        for (var shape : new TreeSet<>(reachable)) {
            names.put(shape.getId(), allocate(symbolProvider.toSymbol(shape).getName(), taken));
            if (shape.isUnionShape()) {
                for (var member : shape.members()) {
                    names.put(member.getId(), allocate(symbolProvider.toSymbol(member).getName(), taken));
                }
            }
        }
        // After every plain form, so adding a streaming member never renames one.
        for (var shape : streaming) {
            asyncNames.put(shape.getId(), allocate(ASYNC_PREFIX + symbolProvider.toSymbol(shape).getName(), taken));
        }
    }

    private void collect(Shape shape, Set<Shape> reachable) {
        switch (shape.getType()) {
            case STRUCTURE, UNION -> {
                if (reachable.add(shape)) {
                    for (var member : shape.members()) {
                        if (isParameter(member)) {
                            collect(model.expectShape(member.getTarget()), reachable);
                        }
                    }
                }
            }
            case LIST -> collect(model.expectShape(shape.asListShape().get().getMember().getTarget()), reachable);
            case MAP -> collect(model.expectShape(shape.asMapShape().get().getValue().getTarget()), reachable);
            default -> {
            }
        }
    }

    private static String allocate(String modelName, Set<String> taken) {
        var separator = "";
        while (!taken.add(modelName + separator + SUFFIX)) {
            separator += "_";
        }
        return modelName + separator + SUFFIX;
    }

    /**
     * @param shape A structure, union, or union member.
     * @return Whether the shape has a dictionary form.
     */
    public boolean hasParams(ToShapeId shape) {
        return names.containsKey(shape.toShapeId());
    }

    /**
     * @param shape A structure or union with a dictionary form, or a member of such a union.
     * @return The symbol of the shape's dictionary form, or of the single-key
     *     dictionary that sets a union member.
     */
    public Symbol paramsSymbol(ToShapeId shape) {
        return modelsSymbol(names.get(shape.toShapeId()));
    }

    /**
     * @param shape A structure.
     * @return Whether the shape is an operation input with a streaming blob member,
     *     which has a second dictionary form for the async client.
     */
    public boolean hasAsyncParams(ToShapeId shape) {
        return asyncNames.containsKey(shape.toShapeId());
    }

    /**
     * @param shape An operation input with a streaming blob member.
     * @return The symbol of the dictionary form whose body may also be an async
     *     stream, which only the async client accepts.
     */
    public Symbol asyncParamsSymbol(ToShapeId shape) {
        return modelsSymbol(asyncNames.get(shape.toShapeId()));
    }

    private Symbol modelsSymbol(String name) {
        return Symbol.builder()
                .name(name)
                .namespace(modelsNamespace, ".")
                .definitionFile("./src/" + modelsNamespace.replace('.', '/') + ".py")
                .build();
    }

    /**
     * @param member The member to check.
     * @return Whether the member is a streaming blob, the body of a request.
     */
    public boolean isStreamingBlob(MemberShape member) {
        var target = model.expectShape(member.getTarget());
        return target.isBlobShape() && target.hasTrait(StreamingTrait.class);
    }

    /**
     * Whether a member of an input shape is written by the caller.
     *
     * <p>Events are sent through the stream an operation returns, so an event stream
     * member is not.
     *
     * @param member The member to check.
     * @return Whether the member is a keyword argument or dictionary key.
     */
    public boolean isParameter(MemberShape member) {
        var target = model.expectShape(member.getTarget());
        return !(target.isUnionShape() && target.hasTrait(StreamingTrait.class));
    }

    /**
     * Whether a member must be set by the caller.
     *
     * <p>Unlike the generated models, which follow Smithy in keeping members of
     * input structures and {@code @clientOptional} members optional, keyword inputs
     * enforce {@code @required}. A member with a default may be omitted, and so may
     * an operation's idempotency token, which the client fills in.
     *
     * <p>CAUTION: smithy_core._dynamic_models.ModelRegistry enforces the same rule
     * at runtime.
     *
     * @param member The member to check.
     * @return Whether the member is a required parameter or key.
     */
    public boolean mustBeSet(MemberShape member) {
        if (!member.hasTrait(RequiredTrait.class)
                || member.getMemberTrait(model, DefaultTrait.class).isPresent()) {
            return false;
        }
        return !(member.getMemberTrait(model, IdempotencyTokenTrait.class).isPresent()
                && operationIndex.isInputStructure(model.expectShape(member.getContainer())));
    }

    /**
     * Spells the type a caller may pass for a member.
     *
     * <p>A structure or union is its model or its dictionary form. Lists and maps
     * are read-only {@code Sequence} and {@code Mapping}, which, unlike {@code list}
     * and {@code dict}, accept a collection of models, of dictionaries, or of both.
     *
     * @param member The member to spell the type of.
     * @param render Renders a symbol as it is referred to in the file being written.
     * @return The type expression.
     */
    public String typeOf(MemberShape member, Function<Symbol, String> render) {
        return typeOf(model.expectShape(member.getTarget()), render);
    }

    private String typeOf(Shape target, Function<Symbol, String> render) {
        return switch (target.getType()) {
            case STRUCTURE, UNION -> render.apply(symbolProvider.toSymbol(target))
                    + " | "
                    + render.apply(paramsSymbol(target));
            case LIST -> render.apply(SEQUENCE) + "["
                    + elementType(target, target.asListShape().get().getMember(), render)
                    + "]";
            case MAP -> render.apply(MAPPING) + "[str, "
                    + elementType(target, target.asMapShape().get().getValue(), render)
                    + "]";
            default -> render.apply(symbolProvider.toSymbol(target));
        };
    }

    private String elementType(Shape collection, MemberShape element, Function<Symbol, String> render) {
        var type = typeOf(element, render);
        return collection.hasTrait(SparseTrait.class) ? type + " | None" : type;
    }
}
