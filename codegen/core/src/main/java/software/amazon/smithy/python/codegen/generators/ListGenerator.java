/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates helper serde functions for lists.
 */
@SmithyInternalApi
public final class ListGenerator implements Runnable {
    private final GenerationContext context;
    private final PythonWriter writer;
    private final ListShape shape;

    public ListGenerator(GenerationContext context, PythonWriter writer, ListShape shape) {
        this.context = context;
        this.writer = writer;
        this.shape = shape;
    }

    @Override
    public void run() {
        generateSerializer();
        generateDeserializer();
    }

    private void generateSerializer() {
        var listSymbol = context.symbolProvider().toSymbol(shape);
        var serializerSymbol = listSymbol.expectProperty(SymbolProperties.SERIALIZER);
        writer.pushState();
        writer.putContext("sparse", shape.hasTrait(SparseTrait.class));
        writer.putContext("propertyName", "e");
        var memberTarget = context.model().expectShape(shape.getMember().getTarget());
        writer.write("""
                def $1L(serializer: $2T, schema: $3T, value: $4T) -> None:
                    member_schema = schema.members["member"]
                    with serializer.begin_list(schema, len(value)) as ls:
                        for e in value:
                            ${?sparse}
                            if e is None:
                                ls.write_null(member_schema)
                            else:
                                ${5C|}
                            ${/sparse}
                            ${^sparse}
                            ${5C|}
                            ${/sparse}

                """,
                serializerSymbol.getName(),
                RuntimeTypes.SHAPE_SERIALIZER,
                RuntimeTypes.SCHEMA,
                listSymbol,
                writer.consumer(w -> memberTarget.accept(
                        new MemberSerializerGenerator(context, w, shape.getMember(), "ls"))));
        writer.popState();
    }

    private void generateDeserializer() {
        var listSymbol = context.symbolProvider().toSymbol(shape);
        var deserializerSymbol = listSymbol.expectProperty(SymbolProperties.DESERIALIZER);
        var memberTarget = context.model().expectShape(shape.getMember().getTarget());

        writer.pushState();
        var sparse = shape.hasTrait(SparseTrait.class);
        writer.putContext("sparse", sparse);
        writer.putContext("includeSchema",
                sparse || (!memberTarget.isUnionShape() && !memberTarget.isStructureShape()));
        writer.write("""
                def $1L(deserializer: $2T, schema: $3T) -> $4T:
                    result: $4T = []
                    ${?includeSchema}
                    member_schema = schema.members["member"]
                    ${/includeSchema}
                    def _read_value(d: $2T):
                        if d.is_null():
                            d.read_null()
                            ${?sparse}result.append(None)${/sparse}
                        else:
                            result.append(${5C|})
                    deserializer.read_list(schema, _read_value)
                    return result
                """,
                deserializerSymbol.getName(),
                RuntimeTypes.SHAPE_DESERIALIZER,
                RuntimeTypes.SCHEMA,
                listSymbol,
                writer.consumer(w -> memberTarget.accept(
                        new MemberDeserializerGenerator(context, w, shape.getMember(), "d"))));
        writer.popState();
    }
}
