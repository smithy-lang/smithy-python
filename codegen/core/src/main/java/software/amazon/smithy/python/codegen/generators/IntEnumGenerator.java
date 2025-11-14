/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.directed.GenerateIntEnumDirective;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class IntEnumGenerator implements Runnable {

    private final GenerateIntEnumDirective<GenerationContext, PythonSettings> directive;

    public IntEnumGenerator(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        this.directive = directive;
    }

    @Override
    public void run() {
        var enumSymbol = directive.symbol().expectProperty(SymbolProperties.ENUM_SYMBOL);
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            writer.addStdlibImport("enum", "IntEnum");
            writer.openBlock("class $L(IntEnum):", "", enumSymbol.getName(), () -> {
                directive.shape().getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(trait.getValue(), directive.context());
                });

                for (MemberShape member : directive.shape().members()) {
                    var name = directive.symbolProvider().toMemberName(member);
                    var value = member.expectTrait(EnumValueTrait.class).expectIntValue();
                    writer.write("$L = $L\n", name, value);
                    member.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                        writer.writeDocs(trait.getValue(), directive.context());
                    });
                }
            });
        });
    }
}
