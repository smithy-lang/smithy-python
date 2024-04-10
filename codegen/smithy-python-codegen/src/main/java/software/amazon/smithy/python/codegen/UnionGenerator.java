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
import software.amazon.smithy.model.traits.StringTrait;

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
        writer.addStdlibImport("dataclasses", "dataclass");

        var memberNames = new ArrayList<String>();
        for (MemberShape member : shape.members()) {
            var memberSymbol = symbolProvider.toSymbol(member);
            memberNames.add(memberSymbol.getName());

            var target = model.expectShape(member.getTarget());
            var targetSymbol = symbolProvider.toSymbol(target);

            writer.write("""
                    @dataclass
                    class $L:
                        ${C|}

                        value: $T

                    """,
                    memberSymbol.getName(),
                    writer.consumer(w -> member.getMemberTrait(model, DocumentationTrait.class)
                            .map(StringTrait::getValue).ifPresent(w::writeDocs)),
                    targetSymbol);
        }

        // Note that the unknown variant doesn't implement __eq__. This is because
        // the default implementation does exactly what we want: an instance check.
        // Since the underlying value is unknown and un-comparable, that is the only
        // realistic implementation.
        var unknownSymbol = symbolProvider.toSymbol(shape).expectProperty("unknown", Symbol.class);
        writer.write("""
                @dataclass
                class $1L:
                    \"""Represents an unknown variant.

                    If you receive this value, you will need to update your library to receive the
                    parsed value.

                    This value may not be deliberately sent.
                    \"""

                    tag: str

                """, unknownSymbol.getName());
        memberNames.add(unknownSymbol.getName());

        shape.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeComment(trait.getValue()));
        writer.addStdlibImport("typing", "Union");
        writer.write("$L = Union[$L]", parentName, String.join(", ", memberNames));

    }
}
