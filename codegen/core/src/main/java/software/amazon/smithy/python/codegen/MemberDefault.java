/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.node.NodeType;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A modeled member default, shared by dataclass fields and operation parameters.
 *
 * @param value the Python expression for the default value itself. This is never
 *     wrapped in a {@code lambda:}; callers that need a callable, such as a dataclass
 *     {@code default_factory}, add that themselves.
 * @param factory whether the value must be constructed per instance rather than shared.
 *     Mutable defaults (collections and documents) must not be shared.
 * @param nullable whether the member accepts {@code None}. Only a {@code @default: null}
 *     member on a non-document target is nullable.
 */
@SmithyInternalApi
public record MemberDefault(String value, boolean factory, boolean nullable) {

    /**
     * Determines whether a member's default must be constructed per instance.
     *
     * <p>This is a pure function of the model: unlike {@link #of}, it registers no
     * imports and needs no writer, so it is safe to call as a predicate.
     *
     * @param context the generation context.
     * @param member the member to inspect. It must have a {@link DefaultTrait}.
     * @return true if the default is mutable and must not be shared between instances.
     */
    public static boolean usesFactory(GenerationContext context, MemberShape member) {
        if (context.model().expectShape(member.getTarget()).isDocumentShape()) {
            // Documents are mutable no matter what the default node holds.
            return true;
        }
        var type = member.expectTrait(DefaultTrait.class).toNode().getType();
        return type == NodeType.ARRAY || type == NodeType.OBJECT;
    }

    public static MemberDefault of(GenerationContext context, PythonWriter writer, MemberShape member) {
        var model = context.model();
        var symbols = context.symbolProvider();
        var node = member.expectTrait(DefaultTrait.class).toNode();
        var target = model.expectShape(member.getTarget());
        // A null document default is a fresh Document(None), not Python None.
        if (!target.isDocumentShape() && node.isNullNode()) {
            return new MemberDefault("None", false, true);
        }
        if (target.isTimestampShape()) {
            var value = CodegenUtils.parseTimestampNode(model, member, node);
            return new MemberDefault(CodegenUtils.getDatetimeConstructor(writer, value), false, false);
        } else if (target.isBlobShape()) {
            writer.addStdlibImport("base64", "b64decode");
            return new MemberDefault(String.format("b64decode(\"%s\")", node.expectStringNode().getValue()),
                    false,
                    false);
        } else if (target.isEnumShape() || target.isIntEnumShape()) {
            var symbol = symbols.toSymbol(target).expectProperty(SymbolProperties.ENUM_SYMBOL);
            return new MemberDefault(String.format("%s(%s)", writer.format("$T", symbol), Node.printJson(node)),
                    false,
                    false);
        } else if (target.isDocumentShape()) {
            var value = switch (node.getType()) {
                case NULL -> "None";
                case BOOLEAN -> node.expectBooleanNode().getValue() ? "True" : "False";
                case ARRAY -> "list()";
                case OBJECT -> "dict()";
                default -> Node.printJson(node);
            };
            return new MemberDefault(String.format("%s(%s)",
                    writer.format("$T", RuntimeTypes.DOCUMENT),
                    value), true, false);
        }
        return switch (node.getType()) {
            case BOOLEAN -> new MemberDefault(node.expectBooleanNode().getValue() ? "True" : "False", false, false);
            // Smithy permits only empty collection defaults.
            case ARRAY -> new MemberDefault("[]", true, false);
            case OBJECT -> new MemberDefault("{}", true, false);
            default -> new MemberDefault(Node.printJson(node), false, false);
        };
    }
}
