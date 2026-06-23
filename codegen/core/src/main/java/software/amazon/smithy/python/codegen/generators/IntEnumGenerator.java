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
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders intEnums as an {@code IntEnum} subclass.
 *
 * <p>The {@code UnknownEnumMixin} base from smithy-core handles values that
 * weren't known at generation time: deserializing an unrecognized value (or
 * filling a missing required member during client error correction, see
 * {@link MemberErrorCorrectionGenerator}) produces a pseudo-member with
 * {@code is_unknown} set rather than raising.
 *
 * @see <a href="https://smithy.io/2.0/spec/simple-types.html#intenum">Smithy spec: intEnum</a>
 */
@SmithyInternalApi
public final class IntEnumGenerator implements Runnable {

    private final GenerateIntEnumDirective<GenerationContext, PythonSettings> directive;

    public IntEnumGenerator(GenerateIntEnumDirective<GenerationContext, PythonSettings> directive) {
        this.directive = directive;
    }

    @Override
    public void run() {
        var enumSymbol = directive.symbol();
        directive.context().writerDelegator().useShapeWriter(directive.shape(), writer -> {
            writer.addStdlibImport("enum", "IntEnum");
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addLocallyDefinedSymbol(enumSymbol);
            writer.openBlock("class $L($T, IntEnum):", "", enumSymbol.getName(), RuntimeTypes.UNKNOWN_ENUM_MIXIN, () -> {
                directive.shape().getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(trait.getValue(), directive.context());
                });

                for (MemberShape member : directive.shape().members()) {
                    var name = directive.symbolProvider().toMemberName(member);
                    var value = member.expectTrait(EnumValueTrait.class).expectIntValue();
                    writer.write("$L = $L", name, value);
                    member.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                        writer.writeDocs(trait.getValue(), directive.context());
                    });
                }
            });
        });
    }
}
