/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.ArrayList;
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.CollectionShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders the type a member accepts as an operation parameter or a {@code Params} key.
 *
 * <p>A structure or union accepts its model or its {@code Params} form, at any depth.
 * Collections are {@code Sequence} and {@code Mapping} rather than {@code list} and
 * {@code dict}, because those are invariant and would reject a list of models where
 * the element type also allows a dictionary.
 */
@SmithyInternalApi
public final class ParamTypeRenderer {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final ParamsIndex paramsIndex;

    /**
     * @param context The generation context.
     */
    public ParamTypeRenderer(GenerationContext context) {
        this(context.model(), context.symbolProvider(), ParamsIndex.of(context));
    }

    /**
     * @param model The model being generated.
     * @param symbolProvider The symbol provider that names the model classes.
     * @param paramsIndex The index naming the Params forms.
     */
    public ParamTypeRenderer(Model model, SymbolProvider symbolProvider, ParamsIndex paramsIndex) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.paramsIndex = paramsIndex;
    }

    /**
     * A structure member as an operation method's keyword parameter or a {@code Params}
     * TypedDict key. Both are built by {@link #parameters} so they can't drift apart.
     *
     * @param member The member.
     * @param name The parameter or key name, which is also the model's field name.
     * @param type The rendered type, without {@code | None}.
     * @param required Whether the parameter has no default, or the key is {@code Required}.
     */
    public record Parameter(MemberShape member, String name, String type, boolean required) {}

    /**
     * Lists a structure's members as parameters, in model order, leaving out an
     * operation input's event stream member.
     *
     * @param writer The writer the types are written to, which imports the symbols they use.
     * @param shape The structure.
     * @param typeCheckingOnly Whether to import the symbols only under {@code TYPE_CHECKING}.
     * @return Returns the parameters.
     */
    public List<Parameter> parameters(PythonWriter writer, StructureShape shape, boolean typeCheckingOnly) {
        var parameters = new ArrayList<Parameter>();
        for (MemberShape member : paramsIndex.getMembers(shape)) {
            parameters.add(new Parameter(
                    member,
                    symbolProvider.toMemberName(member),
                    render(writer, member, typeCheckingOnly),
                    CodegenUtils.isRequiredParameter(model, member)));
        }
        return parameters;
    }

    /**
     * Renders a member's type, without {@code | None} for an optional member.
     *
     * @param writer The writer the type is written to, which imports the symbols it uses.
     * @param member The member to render.
     * @param typeCheckingOnly Whether to import the symbols only under {@code TYPE_CHECKING}.
     * @return Returns the type, to be written with {@code $L}.
     */
    public String render(PythonWriter writer, MemberShape member, boolean typeCheckingOnly) {
        var symbolFormat = symbolFormat(typeCheckingOnly);
        var target = model.expectShape(member.getTarget());
        if (target.isStructureShape() || target.isUnionShape()) {
            return writer.format(symbolFormat + " | " + symbolFormat,
                    symbolProvider.toSymbol(target),
                    paramsIndex.getParamsSymbol(target));
        }
        if (target instanceof CollectionShape collection) {
            return writer.format(symbolFormat + "[$L]",
                    RuntimeTypes.SEQUENCE,
                    renderElement(writer, target, collection.getMember(), typeCheckingOnly));
        }
        if (target instanceof MapShape map) {
            return writer.format(symbolFormat + "[str, $L]",
                    RuntimeTypes.MAPPING,
                    renderElement(writer, target, map.getValue(), typeCheckingOnly));
        }
        if (target.isDocumentShape()) {
            return writer.format(symbolFormat + " | " + symbolFormat,
                    RuntimeTypes.DOCUMENT,
                    RuntimeTypes.DOCUMENT_VALUE);
        }
        return writer.format(symbolFormat, memberSymbol(member, target));
    }

    /**
     * @param typeCheckingOnly Whether symbols are imported only under {@code TYPE_CHECKING}.
     * @return Returns the formatter that writes a symbol: {@code $A} or {@code $T}.
     */
    static String symbolFormat(boolean typeCheckingOnly) {
        return typeCheckingOnly ? "$A" : "$T";
    }

    private String renderElement(
            PythonWriter writer,
            Shape collection,
            MemberShape element,
            boolean typeCheckingOnly
    ) {
        var rendered = render(writer, element, typeCheckingOnly);
        return collection.hasTrait(SparseTrait.class) ? rendered + " | None" : rendered;
    }

    private Symbol memberSymbol(MemberShape member, Shape target) {
        // A union member's own symbol is its variant class, not the value type.
        if (model.expectShape(member.getContainer()).isUnionShape()) {
            return symbolProvider.toSymbol(target);
        }
        return symbolProvider.toSymbol(member);
    }
}
