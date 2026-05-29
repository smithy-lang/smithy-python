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
 * Renders enums as a {@code StrEnum} subclass.
 *
 * <p>Beyond the named members, the generated class has:
 * <ul>
 *   <li>{@code is_unknown} — public. {@code True} when the value didn't come
 *       from a known member: either the service returned a value newer than
 *       this SDK or client error correction filled in a placeholder.</li>
 *   <li>{@code _missing_} — invoked when deserializing a value the SDK
 *       doesn't recognize.</li>
 *   <li>{@code _unknown} — invoked from {@link MemberErrorCorrectionGenerator}
 *       to fill a missing required member.</li>
 *   <li>{@code __eq__} / {@code __hash__} — overridden so an unknown value
 *       is not equal to any known member, even if its underlying string
 *       happens to match one.</li>
 * </ul>
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
        var enumSymbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.ENUM_SYMBOL);
        context.writerDelegator().useShapeWriter(shape, writer -> {
            writer.addStdlibImport("enum", "StrEnum");
            writer.addStdlibImport("typing", "Self");
            writer.openBlock("class $L(StrEnum):", "", enumSymbol.getName(), () -> {
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

                writer.write("""

                        @classmethod
                        def _unknown(cls, value: str) -> "Self":
                            pseudo = str.__new__(cls, value)
                            pseudo._name_ = f"<smithy-unknown:{value}>"
                            pseudo._value_ = value
                            return pseudo

                        @classmethod
                        def _missing_(cls, value: object) -> "Self | None":
                            if isinstance(value, str):
                                return cls._unknown(value)
                            return None

                        @property
                        def is_unknown(self) -> bool:
                            \"""True if this value was not known at SDK generation time.\"""
                            return self._name_ not in type(self).__members__

                        def __eq__(self, other: object) -> bool:
                            if self.is_unknown:
                                return (
                                    isinstance(other, type(self))
                                    and other.is_unknown
                                    and self._value_ == other._value_
                                )
                            if isinstance(other, type(self)) and other.is_unknown:
                                return False
                            return super().__eq__(other)

                        def __hash__(self) -> int:
                            if self.is_unknown:
                                return hash(("<smithy-unknown>", type(self).__name__, self._value_))
                            return super().__hash__()
                        """);
            });
        });
    }
}
