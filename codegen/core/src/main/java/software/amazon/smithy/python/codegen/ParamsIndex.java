/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.KnowledgeIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.CollectionShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.ToShapeId;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Knowledge index of the {@code Params} TypedDicts: which shapes have one and what
 * each is named.
 *
 * <p>Every structure and union reachable from an operation input has one, found by
 * walking structure and union members, list members, and map values, starting at the
 * input itself. The input's event stream member is not a parameter, so it is neither
 * walked nor a key.
 *
 * <p>The runtime resolves the same names, so the naming here MUST match smithy-core's
 * {@code ModelRegistry.params_name}; {@code smithy_test.verify_models} checks the
 * generated {@code _params.pyi} against it.
 */
@SmithyInternalApi
public final class ParamsIndex implements KnowledgeIndex {

    private static final String SUFFIX = "Params";

    private final Set<Shape> shapes = new TreeSet<>();
    private final Map<ShapeId, Symbol> symbols = new HashMap<>();
    private final Model model;

    private ParamsIndex(Model model, PythonSettings settings, SymbolProvider symbolProvider) {
        this.model = model;
        var service = settings.service(model);
        var pending = new ArrayDeque<Shape>();
        for (OperationShape operation : TopDownIndex.of(model).getContainedOperations(service)) {
            pending.add(model.expectShape(operation.getInputShape()));
        }
        while (!pending.isEmpty()) {
            var shape = pending.poll();
            if (!shapes.add(shape)) {
                continue;
            }
            for (MemberShape member : shape.members()) {
                if (!CodegenUtils.isEventStreamMember(model, member)) {
                    addTarget(model, model.expectShape(member.getTarget()), pending);
                }
            }
        }

        var taken = modelNames(model, service, symbolProvider);
        var namespace = settings.moduleName() + "._params";
        var definitionFile = String.format("./src/%s/_params.pyi", settings.moduleName());
        for (Shape shape : shapes) {
            symbols.put(shape.getId(),
                    paramsSymbol(symbolProvider.toSymbol(shape).getName(), taken, namespace, definitionFile));
            if (shape.isUnionShape()) {
                for (MemberShape member : shape.members()) {
                    symbols.put(member.getId(),
                            paramsSymbol(
                                    symbolProvider.toSymbol(member).getName(),
                                    taken,
                                    namespace,
                                    definitionFile));
                }
            }
        }
    }

    private static void addTarget(Model model, Shape target, ArrayDeque<Shape> pending) {
        if (target instanceof StructureShape || target instanceof UnionShape) {
            pending.add(target);
        } else if (target instanceof CollectionShape collection) {
            addTarget(model, model.expectShape(collection.getMember().getTarget()), pending);
        } else if (target instanceof MapShape map) {
            addTarget(model, model.expectShape(map.getValue().getTarget()), pending);
        }
    }

    // Every name the models module defines, so a Params name never shadows one.
    private static Set<String> modelNames(Model model, Shape service, SymbolProvider symbolProvider) {
        var names = new HashSet<String>();
        for (Shape shape : new Walker(model).walkShapes(service)) {
            if (!(shape.isStructureShape() || shape.isUnionShape()
                    || shape.isEnumShape()
                    || shape.isIntEnumShape())) {
                continue;
            }
            names.add(shape.getId().getName());
            var symbol = symbolProvider.toSymbol(shape);
            names.add(symbol.getProperty(SymbolProperties.ENUM_SYMBOL).orElse(symbol).getName());
            if (shape.isUnionShape()) {
                for (MemberShape member : shape.members()) {
                    names.add(symbolProvider.toSymbol(member).getName());
                }
                names.add(symbol.expectProperty(SymbolProperties.UNION_UNKNOWN).getName());
            }
        }
        return names;
    }

    private static Symbol paramsSymbol(String base, Set<String> taken, String namespace, String definitionFile) {
        var name = taken.contains(base + SUFFIX) ? base + "_" + SUFFIX : base + SUFFIX;
        return Symbol.builder()
                .name(name)
                .namespace(namespace, ".")
                .definitionFile(definitionFile)
                .build();
    }

    /**
     * Gets the index for the service being generated, computing it once per model.
     *
     * @param context The generation context.
     * @return Returns the index.
     */
    public static ParamsIndex of(GenerationContext context) {
        return of(context.model(), context.settings(), context.symbolProvider());
    }

    /**
     * Gets the index for the service being generated, computing it once per model.
     *
     * <p>The index is cached on the model, so only the first call's settings and
     * symbol provider are used. Generators use {@link #of(GenerationContext)}.
     *
     * @param model The model being generated.
     * @param settings The settings naming the service and module being generated.
     * @param symbolProvider The symbol provider that names the model classes.
     * @return Returns the index.
     */
    static ParamsIndex of(Model model, PythonSettings settings, SymbolProvider symbolProvider) {
        return model.getKnowledge(ParamsIndex.class, m -> new ParamsIndex(m, settings, symbolProvider));
    }

    /**
     * @return Returns every structure and union with a {@code Params} form, ordered by shape id.
     */
    public Set<Shape> getShapes() {
        return Collections.unmodifiableSet(shapes);
    }

    /**
     * @return Returns every {@code Params} name, sorted: the TypedDicts and the union aliases.
     */
    public Set<String> getNames() {
        var names = new TreeSet<String>();
        for (Symbol symbol : symbols.values()) {
            names.add(symbol.getName());
        }
        return names;
    }

    /**
     * Gets the {@code Params} TypedDict of a structure, or the alias of a union's
     * variant TypedDicts.
     *
     * @param shape The structure or union.
     * @return Returns the symbol, defined in {@code _params.pyi}.
     */
    public Symbol getParamsSymbol(ToShapeId shape) {
        return expectSymbol(shape.toShapeId());
    }

    /**
     * Gets the single-key {@code Params} TypedDict of a union variant.
     *
     * @param member The union member.
     * @return Returns the symbol, defined in {@code _params.pyi}.
     */
    public Symbol getVariantParamsSymbol(MemberShape member) {
        return expectSymbol(member.getId());
    }

    /**
     * Gets the members of a structure that are parameters or {@code Params} keys,
     * in model order. This leaves out an event stream member, which isn't a field.
     *
     * @param shape The structure.
     * @return Returns the members.
     */
    public List<MemberShape> getMembers(StructureShape shape) {
        var members = new ArrayList<MemberShape>();
        for (MemberShape member : shape.members()) {
            if (!CodegenUtils.isEventStreamMember(model, member)) {
                members.add(member);
            }
        }
        return members;
    }

    private Symbol expectSymbol(ShapeId id) {
        var symbol = symbols.get(id);
        if (symbol == null) {
            throw new CodegenException(id + " is not reachable from an operation input, so it has no Params form.");
        }
        return symbol;
    }
}
