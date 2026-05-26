/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

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
public final class MemberErrorCorrectionGenerator extends ShapeVisitor.DataShapeVisitor<Boolean> {

    private final GenerationContext context;
    private final PythonWriter writer;

    public MemberErrorCorrectionGenerator(GenerationContext context, PythonWriter writer) {
        this.context = context;
        this.writer = writer;
    }

    /**
     * @return {@code true} if the visitor will emit a default expression for this shape.
     */
    public static boolean hasDefault(Shape target) {
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
                    STRING, TIMESTAMP, DOCUMENT, LIST, MAP, ENUM, INT_ENUM, STRUCTURE, UNION ->
                true;
            case BLOB -> !target.hasTrait(StreamingTrait.class);
            default -> false;
        };
    }

    @Override
    public Boolean booleanShape(BooleanShape shape) {
        writer.writeInline("False");
        return true;
    }

    @Override
    public Boolean byteShape(ByteShape shape) {
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean shortShape(ShortShape shape) {
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean integerShape(IntegerShape shape) {
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean longShape(LongShape shape) {
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean bigIntegerShape(BigIntegerShape shape) {
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean floatShape(FloatShape shape) {
        writer.writeInline("0.0");
        return true;
    }

    @Override
    public Boolean doubleShape(DoubleShape shape) {
        writer.writeInline("0.0");
        return true;
    }

    @Override
    public Boolean bigDecimalShape(BigDecimalShape shape) {
        writer.addStdlibImport("decimal", "Decimal");
        writer.writeInline("Decimal(0)");
        return true;
    }

    @Override
    public Boolean stringShape(StringShape shape) {
        writer.writeInline("\"\"");
        return true;
    }

    @Override
    public Boolean blobShape(BlobShape shape) {
        writer.writeInline("b\"\"");
        return true;
    }

    @Override
    public Boolean timestampShape(TimestampShape shape) {
        writer.addStdlibImport("datetime", "datetime");
        writer.addStdlibImport("datetime", "timezone");
        writer.writeInline("datetime.fromtimestamp(0, tz=timezone.utc)");
        return true;
    }

    @Override
    public Boolean documentShape(DocumentShape shape) {
        writer.addImport("smithy_core.documents", "Document");
        writer.writeInline("Document(None)");
        return true;
    }

    @Override
    public Boolean listShape(ListShape shape) {
        writer.writeInline("[]");
        return true;
    }

    @Override
    public Boolean mapShape(MapShape shape) {
        writer.writeInline("{}");
        return true;
    }

    @Override
    public Boolean enumShape(EnumShape shape) {
        // TODO: the Smithy spec recommends enum types define an unknown variant. If a
        //   future change adds an unknown variant to the generated enum class (e.g.
        //   MyEnum.unknown(value)), revisit this to emit it instead of the bare "".
        writer.writeInline("\"\"");
        return true;
    }

    @Override
    public Boolean intEnumShape(IntEnumShape shape) {
        // TODO: the Smithy spec recommends intEnum types define an unknown variant. If a
        //   future change adds an unknown variant to the generated intEnum class (e.g.
        //   MyIntEnum.unknown(value)), revisit this to emit it instead of the bare 0.
        writer.writeInline("0");
        return true;
    }

    @Override
    public Boolean unionShape(UnionShape shape) {
        var unknownSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.UNION_UNKNOWN);
        writer.addImport(unknownSymbol, unknownSymbol.getName());
        writer.writeInline("$L(tag=\"\")", unknownSymbol.getName());
        return true;
    }

    @Override
    public Boolean structureShape(StructureShape shape) {
        // Delegate to the target struct's _smithy_default() so nested required fields are
        // also filled in. Recursion terminates because Smithy forbids recursive paths whose
        // members are all @required:
        // https://smithy.io/2.0/spec/aggregate-types.html#recursive-shape-definitions
        var symbol = context.symbolProvider().toSymbol(shape);
        writer.addImport(symbol, symbol.getName());
        writer.writeInline("$L._smithy_default()", symbol.getName());
        return true;
    }

    @Override
    public Boolean memberShape(MemberShape shape) {
        return context.model().expectShape(shape.getTarget()).accept(this);
    }
}
