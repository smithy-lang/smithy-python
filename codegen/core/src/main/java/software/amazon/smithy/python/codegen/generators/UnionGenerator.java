/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.Set;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders unions.
 */
@SmithyInternalApi
public final class UnionGenerator implements Runnable {

    private final GenerationContext context;
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final UnionShape shape;
    private final Set<Shape> recursiveShapes;

    public UnionGenerator(
            GenerationContext context,
            PythonWriter writer,
            UnionShape shape,
            Set<Shape> recursiveShapes
    ) {
        this.context = context;
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.writer = writer;
        this.shape = shape;
        this.recursiveShapes = recursiveShapes;
    }

    @Override
    public void run() {
        writer.pushState();
        var parentName = symbolProvider.toSymbol(shape).getName();
        writer.addStdlibImport("dataclasses", "dataclass");
        writer.addImport("smithy_core.serializers", "ShapeSerializer");
        var schemaSymbol = symbolProvider.toSymbol(shape).expectProperty(SymbolProperties.SCHEMA);
        writer.putContext("schema", schemaSymbol);

        var memberNames = new ArrayList<String>();
        for (MemberShape member : shape.members()) {
            var memberSymbol = symbolProvider.toSymbol(member);
            memberNames.add(memberSymbol.getName());

            var target = model.expectShape(member.getTarget());
            var targetSymbol = symbolProvider.toSymbol(target);

            writer.write("""
                    @dataclass
                    class $1L:
                        ${2C|}

                        value: $3T

                        def serialize(self, serializer: ShapeSerializer):
                            serializer.write_struct($4T, self)

                        def serialize_members(self, serializer: ShapeSerializer):
                            ${5C|}

                        @classmethod
                        def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
                            return cls(value=${6C|})

                    """,
                    memberSymbol.getName(),
                    writer.consumer(w -> member.getMemberTrait(model, DocumentationTrait.class)
                            .map(StringTrait::getValue)
                            .ifPresent(w::writeDocs)),
                    targetSymbol,
                    schemaSymbol,
                    writer.consumer(w -> target.accept(
                            new MemberSerializerGenerator(context, w, member, "serializer"))),
                    writer.consumer(w -> target.accept(
                            new MemberDeserializerGenerator(context, w, member, "deserializer")))

            );
        }

        // Note that the unknown variant doesn't implement __eq__. This is because
        // the default implementation does exactly what we want: an instance check.
        // Since the underlying value is unknown and un-comparable, that is the only
        // realistic implementation.
        var unknownSymbol = symbolProvider.toSymbol(shape).expectProperty(SymbolProperties.UNION_UNKNOWN);
        writer.addImport("smithy_core.exceptions", "SmithyException");
        writer.write("""
                @dataclass
                class $1L:
                    \"""Represents an unknown variant.

                    If you receive this value, you will need to update your library to receive the
                    parsed value.

                    This value may not be deliberately sent.
                    \"""

                    tag: str

                    def serialize(self, serializer: ShapeSerializer):
                        raise SmithyException("Unknown union variants may not be serialized.")

                    def serialize_members(self, serializer: ShapeSerializer):
                        raise SmithyException("Unknown union variants may not be serialized.")

                    @classmethod
                    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
                        raise NotImplementedError()

                """, unknownSymbol.getName());
        memberNames.add(unknownSymbol.getName());

        writer.write("type $L = $L\n", parentName, String.join(" | ", memberNames));
        shape.getTrait(DocumentationTrait.class).ifPresent(trait -> writer.writeDocs(trait.getValue()));

        generateDeserializer();
        writer.popState();
    }

    private void generateDeserializer() {
        writer.addLogger();
        writer.addStdlibImports("typing", Set.of("Self", "Any"));
        writer.addImport("smithy_core.deserializers", "ShapeDeserializer");
        writer.addImport("smithy_core.exceptions", "SmithyException");

        // TODO: add in unknown handling

        var symbol = symbolProvider.toSymbol(shape);
        var deserializerSymbol = symbol.expectProperty(SymbolProperties.DESERIALIZER);
        var schemaSymbol = symbol.expectProperty(SymbolProperties.SCHEMA);
        writer.putContext("schema", schemaSymbol);
        writer.write("""
                class $1L:
                    _result: $2T | None = None

                    def deserialize(self, deserializer: ShapeDeserializer) -> $2T:
                        self._result = None
                        deserializer.read_struct($3T, self._consumer)

                        if self._result is None:
                            raise SmithyException("Unions must have exactly one value, but found none.")

                        return self._result

                    def _consumer(self, schema: Schema, de: ShapeDeserializer) -> None:
                        match schema.expect_member_index():
                            ${4C|}
                            case _:
                                logger.debug(f"Unexpected member schema: {schema}")

                    def _set_result(self, value: $2T) -> None:
                        if self._result is not None:
                            raise SmithyException("Unions must have exactly one value, but found more than one.")
                        self._result = value
                """,
                deserializerSymbol.getName(),
                symbol,
                schemaSymbol,
                writer.consumer(w -> deserializeMembers()));
    }

    private void deserializeMembers() {
        int index = 0;
        for (MemberShape member : shape.members()) {
            writer.write("""
                    case $L:
                        self._set_result($T.deserialize(de))
                    """, index++, symbolProvider.toSymbol(member));
        }
    }
}
