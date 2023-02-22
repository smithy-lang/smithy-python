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

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.directed.GenerateIntEnumDirective;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;

final class IntEnumGenerator implements Runnable {

    private final GenerateIntEnumDirective<GenerationContext, PythonSettings> directive;

    IntEnumGenerator(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        this.directive = directive;
    }

    @Override
    public void run() {
        var enumSymbol = directive.symbol().expectProperty("enumSymbol", Symbol.class);
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            writer.addStdlibImport("enum", "IntEnum");
            writer.openBlock("class $L(IntEnum):", "", enumSymbol.getName(), () -> {
                directive.shape().getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(writer.formatDocs(trait.getValue()));
                });

                for (MemberShape member : directive.shape().members()) {
                    member.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeComment(trait.getValue()));
                    var name = directive.symbolProvider().toMemberName(member);
                    var value = member.expectTrait(EnumValueTrait.class).expectIntValue();
                    writer.write("$L = $L\n", name, value);
                }
            });
        });
    }
}
