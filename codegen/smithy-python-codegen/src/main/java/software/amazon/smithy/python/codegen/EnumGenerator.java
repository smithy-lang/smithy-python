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

import java.util.Iterator;
import java.util.Locale;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.EnumShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;

/**
 * Renders enums.
 */
final class EnumGenerator implements Runnable {
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final EnumShape shape;

    EnumGenerator(Model model, SymbolProvider symbolProvider, PythonWriter writer, EnumShape enumShape) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = enumShape;
    }

    @Override
    public void run() {
        var enumSymbol = symbolProvider.toSymbol(shape).expectProperty("enumSymbol", Symbol.class);
        writer.openBlock("class $L:", "", enumSymbol.getName(), () -> {
            shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                writer.writeDocs(writer.formatDocs(trait.getValue()));
            });

            for (MemberShape member: shape.members()) {
                member.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeComment(trait.getValue()));
                var name = symbolProvider.toMemberName(member);
                writer.write("$L = $S\n", name, getEnumValue(member));
            }

            writer.writeComment("""
                This set contains every possible value known at the time this was \
                generated. New values may be added in the future.""");
            writer.writeInline("values = frozenset({");
            for (Iterator<MemberShape> iter = shape.members().iterator(); iter.hasNext();) {
                writer.writeInline("$S", getEnumValue(iter.next()));
                if (iter.hasNext()) {
                    writer.writeInline(", ");
                }
            }
            writer.writeInline("})\n");
        });
    }

    public String getEnumValue(MemberShape member) {
        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-enumvalue-trait
        return member.getTrait(EnumValueTrait.class)
                .flatMap(EnumValueTrait::getStringValue)
                .orElseGet(() -> member.getMemberName().toUpperCase(Locale.ENGLISH));
    }
}
