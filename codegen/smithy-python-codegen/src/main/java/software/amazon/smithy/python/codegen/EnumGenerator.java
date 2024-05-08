/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.model.shapes.EnumShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;

/**
 * Renders enums.
 */
final class EnumGenerator implements Runnable {
    private final EnumShape shape;
    private final GenerationContext context;

    EnumGenerator(GenerationContext context, EnumShape enumShape) {
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
