/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates helper serde functions for maps.
 */
@SmithyInternalApi
public final class MapGenerator implements Runnable {
    private final GenerationContext context;
    private final PythonWriter writer;
    private final MapShape shape;

    public MapGenerator(GenerationContext context, PythonWriter writer, MapShape shape) {
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
        var mapSymbol = context.symbolProvider().toSymbol(shape);
        var serializerSymbol = mapSymbol.expectProperty(SymbolProperties.SERIALIZER);
        writer.pushState();
        writer.addImport("smithy_core.serializers", "ShapeSerializer");
        writer.addImport("smithy_core.schemas", "Schema");
        writer.putContext("sparse", shape.hasTrait(SparseTrait.class));
        writer.putContext("propertyName", "v");
        var valueTarget = context.model().expectShape(shape.getValue().getTarget());

        // Note that we have to disable typing in the sparse case because pyright for some reason isn't
        // narrowing out the None even though there's an explicit is None check.
        writer.write("""
                def $1L(serializer: ShapeSerializer, schema: Schema, value: $2T) -> None:
                    with serializer.begin_map(schema, len(value)) as m:
                        value_schema = schema.members["value"]
                        for k, v in value.items():
                            ${?sparse}
                            if v is None:
                                m.entry(k, lambda vs: vs.write_null(value_schema))
                            else:
                                m.entry(k, lambda vs: ${3C|})  # type: ignore
                            ${/sparse}
                            ${^sparse}
                            m.entry(k, lambda vs: ${3C|})
                            ${/sparse}

                """,
                serializerSymbol.getName(),
                mapSymbol,
                writer.consumer(w -> valueTarget.accept(
                        new MemberSerializerGenerator(context, w, shape.getValue(), "vs"))));
        writer.popState();
    }

    private void generateDeserializer() {
        var listSymbol = context.symbolProvider().toSymbol(shape);
        var deserializerSymbol = listSymbol.expectProperty(SymbolProperties.DESERIALIZER);
        var valueTarget = context.model().expectShape(shape.getValue().getTarget());

        writer.pushState();
        writer.addImport("smithy_core.serializers", "ShapeSerializer");
        writer.addImport("smithy_core.schemas", "Schema");
        var sparse = shape.hasTrait(SparseTrait.class);
        writer.putContext("sparse", sparse);
        writer.putContext("includeSchema", sparse || (!valueTarget.isUnionShape() && !valueTarget.isStructureShape()));
        writer.write("""
                def $1L(deserializer: ShapeDeserializer, schema: Schema) -> $2T:
                    result: $2T = {}
                    value_schema = schema.members["value"]
                    def _read_value(k: str, d: ShapeDeserializer):
                        if d.is_null():
                            d.read_null()
                            ${?sparse}result[k] = None${/sparse}
                        else:
                            result[k] = ${3C|}
                    deserializer.read_map(schema, _read_value)
                    return result
                """,
                deserializerSymbol.getName(),
                listSymbol,
                writer.consumer(w -> valueTarget.accept(
                        new MemberDeserializerGenerator(context, w, shape.getValue(), "d"))));
        writer.popState();
    }
}
