/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.model.shapes.EnumShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders enums as a {@code StrEnum} subclass.
 *
 * <p>The {@code UnknownEnumMixin} base from smithy-core handles values that
 * weren't known at generation time: deserializing an unrecognized value (or
 * filling a missing required member during client error correction, see
 * {@link MemberErrorCorrectionGenerator}) produces a pseudo-member with
 * {@code is_unknown} set rather than raising.
 *
 * @see <a href="https://smithy.io/2.0/spec/simple-types.html#enum">Smithy spec: enum</a>
 */
@SmithyInternalApi
public final class EnumGenerator implements Runnable {
    private final EnumShape shape;
    private final GenerationContext context;

    public EnumGenerator(GenerationContext context, EnumShape enumShape) {
        this.context = context;
        this.shape = enumShape;
    }

    @Override
    public void run() {
        var enumSymbol = context.symbolProvider().toSymbol(shape);
        context.writerDelegator().useShapeWriter(shape, writer -> {
            writer.addStdlibImport("enum", "StrEnum");
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addLocallyDefinedSymbol(enumSymbol);
            writer.openBlock("class $L($T, StrEnum):", "", enumSymbol.getName(), RuntimeTypes.UNKNOWN_ENUM_MIXIN, () -> {
                shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(trait.getValue(), context);
                });

                for (MemberShape member : shape.members()) {
                    var name = context.symbolProvider().toMemberName(member);
                    var value = member.expectTrait(EnumValueTrait.class).expectStringValue();
                    writer.write("$L = $S", name, value);
                    member.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                        writer.writeDocs(trait.getValue(), context);
                    });
                }
            });
        });
    }
}
