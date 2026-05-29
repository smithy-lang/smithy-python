/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.shapes.BigDecimalShape;
import software.amazon.smithy.model.shapes.BigIntegerShape;
import software.amazon.smithy.model.shapes.BlobShape;
import software.amazon.smithy.model.shapes.BooleanShape;
import software.amazon.smithy.model.shapes.ByteShape;
import software.amazon.smithy.model.shapes.DocumentShape;
import software.amazon.smithy.model.shapes.DoubleShape;
import software.amazon.smithy.model.shapes.EnumShape;
import software.amazon.smithy.model.shapes.FloatShape;
import software.amazon.smithy.model.shapes.IntEnumShape;
import software.amazon.smithy.model.shapes.IntegerShape;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.LongShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.ShortShape;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.TimestampShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits the Python expression used to fill a missing required member during client error
 * correction.
 *
 * @see <a href="https://smithy.io/2.0/spec/aggregate-types.html#client-error-correction">Smithy
 *     spec: Client error correction</a>
 */
@SmithyInternalApi
public final class MemberErrorCorrectionGenerator extends ShapeVisitor.DataShapeVisitor<Void> {

    private final GenerationContext context;
    private final PythonWriter writer;

    public MemberErrorCorrectionGenerator(GenerationContext context, PythonWriter writer) {
        this.context = context;
        this.writer = writer;
    }

    /**
     * @return {@code true} if the visitor will emit a default expression for this shape.
     */
    public static boolean hasDefault(Shape target, Model model) {
        return switch (target.getType()) {
            // Note on streaming shapes:
            //   - Streaming unions (event streams) are filtered out earlier by
            //     StructureGenerator#filterEventStreamMember and never reach this visitor,
            //     so UNION can unconditionally return true here.
            //   - Streaming blobs are NOT filtered earlier, so we explicitly exclude them
            //     below. Per Smithy spec § 13.3.1, a missing streaming blob is already
            //     handled by the deserializer (an empty HTTP body becomes a zero-length
            //     AsyncBytesReader), so client error correction is unnecessary.
            case BOOLEAN, BYTE, SHORT, INTEGER, LONG, BIG_INTEGER, FLOAT, DOUBLE, BIG_DECIMAL,
                    STRING, TIMESTAMP, DOCUMENT, LIST, MAP, ENUM, INT_ENUM, UNION ->
                true;
            case BLOB -> !target.hasTrait(StreamingTrait.class);
            case STRUCTURE -> structHasDefault((StructureShape) target, model);
            default -> false;
        };
    }

    /**
     * We can build a default for a struct only when we can build a default for each of its
     * required members, so we have to recurse into nested structs. The recursion is safe
     * because Smithy doesn't allow cycles where every member along the path is @required;
     * we'll always reach a base case (a primitive, list, map, etc.) before looping back.
     *
     * See https://smithy.io/2.0/spec/aggregate-types.html#recursive-shape-definitions
     */
    private static boolean structHasDefault(StructureShape struct, Model model) {
        var index = NullableIndex.of(model);
        for (MemberShape member : struct.members()) {
            if (index.isMemberNullable(member) || member.hasTrait(DefaultTrait.class)) {
                continue;
            }
            if (!hasDefault(model.expectShape(member.getTarget()), model)) {
                return false;
            }
        }
        return true;
    }

    @Override
    public Void booleanShape(BooleanShape shape) {
        writer.writeInline("False");
        return null;
    }

    @Override
    public Void byteShape(ByteShape shape) {
        writer.writeInline("0");
        return null;
    }

    @Override
    public Void shortShape(ShortShape shape) {
        writer.writeInline("0");
        return null;
    }

    @Override
    public Void integerShape(IntegerShape shape) {
        writer.writeInline("0");
        return null;
    }

    @Override
    public Void longShape(LongShape shape) {
        writer.writeInline("0");
        return null;
    }

    @Override
    public Void bigIntegerShape(BigIntegerShape shape) {
        writer.writeInline("0");
        return null;
    }

    @Override
    public Void floatShape(FloatShape shape) {
        writer.writeInline("0.0");
        return null;
    }

    @Override
    public Void doubleShape(DoubleShape shape) {
        writer.writeInline("0.0");
        return null;
    }

    @Override
    public Void bigDecimalShape(BigDecimalShape shape) {
        writer.addStdlibImport("decimal", "Decimal");
        writer.writeInline("Decimal(0)");
        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        writer.writeInline("\"\"");
        return null;
    }

    @Override
    public Void blobShape(BlobShape shape) {
        writer.writeInline("b\"\"");
        return null;
    }

    @Override
    public Void timestampShape(TimestampShape shape) {
        writer.addStdlibImport("datetime", "datetime");
        writer.addStdlibImport("datetime", "timezone");
        writer.writeInline("datetime.fromtimestamp(0, tz=timezone.utc)");
        return null;
    }

    @Override
    public Void documentShape(DocumentShape shape) {
        writer.addImport("smithy_core.documents", "Document");
        writer.writeInline("Document(None)");
        return null;
    }

    @Override
    public Void listShape(ListShape shape) {
        writer.writeInline("[]");
        return null;
    }

    @Override
    public Void mapShape(MapShape shape) {
        writer.writeInline("{}");
        return null;
    }

    @Override
    public Void enumShape(EnumShape shape) {
        var enumSymbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.ENUM_SYMBOL);
        writer.addImport(enumSymbol, enumSymbol.getName());
        writer.writeInline("$L._unknown(\"\")", enumSymbol.getName());
        return null;
    }

    @Override
    public Void intEnumShape(IntEnumShape shape) {
        var enumSymbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.ENUM_SYMBOL);
        writer.addImport(enumSymbol, enumSymbol.getName());
        writer.writeInline("$L._unknown(0)", enumSymbol.getName());
        return null;
    }

    @Override
    public Void unionShape(UnionShape shape) {
        var unknownSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.UNION_UNKNOWN);
        writer.addImport(unknownSymbol, unknownSymbol.getName());
        writer.writeInline("$L(tag=\"\")", unknownSymbol.getName());
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        var symbol = context.symbolProvider().toSymbol(shape);
        writer.addImport(symbol, symbol.getName());
        writer.writeInline("$L._smithy_default()", symbol.getName());
        return null;
    }

    @Override
    public Void memberShape(MemberShape shape) {
        return context.model().expectShape(shape.getTarget()).accept(this);
    }
}
