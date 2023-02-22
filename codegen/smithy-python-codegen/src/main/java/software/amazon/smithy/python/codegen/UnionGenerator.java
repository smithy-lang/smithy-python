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

import java.util.ArrayList;
import java.util.Set;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.utils.StringUtils;

/**
 * Renders unions.
 */
final class UnionGenerator implements Runnable {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final UnionShape shape;
    private final Set<Shape> recursiveShapes;

    UnionGenerator(
            Model model,
            SymbolProvider symbolProvider,
            PythonWriter writer,
            UnionShape shape,
            Set<Shape>  recursiveShapes
    ) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = shape;
        this.recursiveShapes = recursiveShapes;
    }

    @Override
    public void run() {
        var parentName = symbolProvider.toSymbol(shape).getName();
        writer.addStdlibImport("typing", "Dict");
        writer.addStdlibImport("typing", "Any");

        var memberNames = new ArrayList<String>();
        for (MemberShape member : shape.members()) {
            var memberSymbol = symbolProvider.toSymbol(member);
            memberNames.add(memberSymbol.getName());

            var target = model.expectShape(member.getTarget());
            var targetSymbol = symbolProvider.toSymbol(target);

            writer.openBlock("class $L():", "", memberSymbol.getName(), () -> {
                member.getMemberTrait(model, DocumentationTrait.class).ifPresent(trait -> {
                    writer.writeDocs(trait.getValue());
                });
                writer.openBlock("def __init__(self, value: $T):", "", targetSymbol, () -> {
                    writer.write("self.value = value");
                });

                writer.openBlock("def as_dict(self) -> Dict[str, Any]:", "", () -> {
                    if (target.isStructureShape() || target.isUnionShape()) {
                        writer.write("return {$S: self.value.as_dict()}", member.getMemberName());
                    } else if (targetSymbol.getProperty("asDict").isPresent()) {
                        var targetAsDictSymbol = targetSymbol.expectProperty("asDict", Symbol.class);
                        writer.write("return {$S: $T(self.value)}", member.getMemberName(), targetAsDictSymbol);
                    } else {
                        writer.write("return {$S: self.value}", member.getMemberName());
                    }
                });

                writer.write("@staticmethod");
                writer.openBlock("def from_dict(d: Dict[str, Any]) -> $S:", "", memberSymbol.getName(), () -> {
                    writer.write("""
                            if (len(d) != 1):
                                raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
                            """);
                    if (target.isStructureShape()) {
                        writer.write("return $T($T.from_dict(d[$S]))", memberSymbol, targetSymbol,
                                member.getMemberName());
                    } else if (targetSymbol.getProperty("fromDict").isPresent()) {
                        var targetFromDictSymbol = targetSymbol.expectProperty("fromDict", Symbol.class);
                        writer.write("return $T($T(d[$S]))",
                            memberSymbol, targetFromDictSymbol, member.getMemberName());
                    } else {
                        writer.write("return $T(d[$S])", memberSymbol, member.getMemberName());
                    }
                });

                writer.write("""
                    def __repr__(self) -> str:
                        return f"$L(value=repr(self.value))"
                    """, memberSymbol.getName());

                writer.write("""
                    def __eq__(self, other: Any) -> bool:
                        if not isinstance(other, $1L):
                            return False
                        return self.value == other.value
                    """, memberSymbol.getName());
            });
            writer.write("");
        }

        // Note that the unknown variant doesn't implement __eq__. This is because
        // the default implementation does exactly what we want: an instance check.
        // Since the underlying value is unknown and un-comparable, that is the only
        // realistic implementation.
        var unknownSymbol = symbolProvider.toSymbol(shape).expectProperty("unknown", Symbol.class);
        writer.write("""
                class $1L():
                    \"""Represents an unknown variant.

                    If you receive this value, you will need to update your library to receive the
                    parsed value.

                    This value may not be deliberately sent.
                    \"""

                    def __init__(self, tag: str):
                        self.tag = tag

                    def as_dict(self) -> Dict[str, Any]:
                        return {"SDK_UNKNOWN_MEMBER": {"name": self.tag}}

                    @staticmethod
                    def from_dict(d: Dict[str, Any]) -> "$1L":
                        if (len(d) != 1):
                            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
                        return $1L(d["SDK_UNKNOWN_MEMBER"]["name"])

                    def __repr__(self) -> str:
                        return f"$1L(tag={self.tag})"
                """, unknownSymbol.getName());
        memberNames.add(unknownSymbol.getName());

        shape.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeComment(trait.getValue()));
        writer.addStdlibImport("typing", "Union");
        writer.write("$L = Union[$L]", parentName, String.join(", ", memberNames));

        writeGlobalFromDict();
    }

    private void writeGlobalFromDict() {
        var parentSymbol = symbolProvider.toSymbol(shape);
        var fromDictSymbol = parentSymbol.expectProperty("fromDict", Symbol.class);
        writer.openBlock("def $L(d: Dict[str, Any]) -> $T:", "", fromDictSymbol.getName(), parentSymbol, () -> {
            for (MemberShape member : shape.members()) {
                var memberName = parentSymbol.getName() + StringUtils.capitalize(member.getMemberName());
                writer.write("""
                        if $S in d:
                            return $L.from_dict(d)
                        """, member.getMemberName(), memberName);
            }
            writer.write("raise TypeError(f'Unions may have exactly 1 value, but found {len(d)}')");
        });
    }
}
