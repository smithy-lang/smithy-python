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
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders enums.
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
        var enumSymbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.ENUM_SYMBOL);
        context.writerDelegator().useShapeWriter(shape, writer -> {
            writer.addStdlibImport("enum", "StrEnum");
            writer.openBlock("class $L(StrEnum):", "", enumSymbol.getName(), () -> {
                shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(writer.formatDocs(trait.getValue()));
                });

                for (MemberShape member : shape.members()) {
                    var name = context.symbolProvider().toMemberName(member);
                    var value = member.expectTrait(EnumValueTrait.class).expectStringValue();
                    writer.write("$L = $S", name, value);
                    member.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeDocs(trait.getValue()));
                }
            });
        });
    }
}
