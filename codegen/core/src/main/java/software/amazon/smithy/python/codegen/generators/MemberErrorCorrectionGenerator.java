/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.function.Consumer;
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
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.ShortShape;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.TimestampShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Produces the Python expression used to fill a missing required member during client error
 * correction.
 *
 * <p>Visiting a shape returns a consumer that writes the default expression, or {@code null}
 * if no default can be synthesized for the shape (a streaming shape, or a structure with a
 * required member that itself has no synthesizable default). Callers decide what to do with
 * unsynthesizable members; the visitor is the single source of truth for what is synthesizable.
 *
 * @see <a href="https://smithy.io/2.0/spec/aggregate-types.html#client-error-correction">Smithy
 *     spec: Client error correction</a>
 */
@SmithyInternalApi
public final class MemberErrorCorrectionGenerator extends ShapeVisitor.DataShapeVisitor<Consumer<PythonWriter>> {

    private final GenerationContext context;

    public MemberErrorCorrectionGenerator(GenerationContext context) {
        this.context = context;
    }

    @Override
    public Consumer<PythonWriter> booleanShape(BooleanShape shape) {
        return writer -> writer.writeInline("False");
    }

    @Override
    public Consumer<PythonWriter> byteShape(ByteShape shape) {
        return writer -> writer.writeInline("0");
    }

    @Override
    public Consumer<PythonWriter> shortShape(ShortShape shape) {
        return writer -> writer.writeInline("0");
    }

    @Override
    public Consumer<PythonWriter> integerShape(IntegerShape shape) {
        return writer -> writer.writeInline("0");
    }

    @Override
    public Consumer<PythonWriter> longShape(LongShape shape) {
        return writer -> writer.writeInline("0");
    }

    @Override
    public Consumer<PythonWriter> bigIntegerShape(BigIntegerShape shape) {
        return writer -> writer.writeInline("0");
    }

    @Override
    public Consumer<PythonWriter> floatShape(FloatShape shape) {
        return writer -> writer.writeInline("0.0");
    }

    @Override
    public Consumer<PythonWriter> doubleShape(DoubleShape shape) {
        return writer -> writer.writeInline("0.0");
    }

    @Override
    public Consumer<PythonWriter> bigDecimalShape(BigDecimalShape shape) {
        return writer -> {
            writer.addStdlibImport("decimal", "Decimal");
            writer.writeInline("Decimal(0)");
        };
    }

    @Override
    public Consumer<PythonWriter> stringShape(StringShape shape) {
        return writer -> writer.writeInline("\"\"");
    }

    @Override
    public Consumer<PythonWriter> blobShape(BlobShape shape) {
        // Per Smithy spec § 13.3.1, a missing streaming blob is already handled by the
        // deserializer (an empty HTTP body becomes a zero-length AsyncBytesReader), so
        // client error correction is unnecessary.
        if (shape.hasTrait(StreamingTrait.class)) {
            return null;
        }
        return writer -> writer.writeInline("b\"\"");
    }

    @Override
    public Consumer<PythonWriter> timestampShape(TimestampShape shape) {
        return writer -> {
            writer.addStdlibImport("datetime", "datetime");
            writer.addStdlibImport("datetime", "timezone");
            writer.writeInline("datetime.fromtimestamp(0, tz=timezone.utc)");
        };
    }

    @Override
    public Consumer<PythonWriter> documentShape(DocumentShape shape) {
        return writer -> {
            writer.addImport("smithy_core.documents", "Document");
            writer.writeInline("Document(None)");
        };
    }

    @Override
    public Consumer<PythonWriter> listShape(ListShape shape) {
        return writer -> writer.writeInline("[]");
    }

    @Override
    public Consumer<PythonWriter> mapShape(MapShape shape) {
        return writer -> writer.writeInline("{}");
    }

    @Override
    public Consumer<PythonWriter> enumShape(EnumShape shape) {
        var enumSymbol = context.symbolProvider().toSymbol(shape);
        return writer -> {
            writer.addImport(enumSymbol, enumSymbol.getName());
            writer.writeInline("$L._unknown(\"\")", enumSymbol.getName());
        };
    }

    @Override
    public Consumer<PythonWriter> intEnumShape(IntEnumShape shape) {
        var enumSymbol = context.symbolProvider().toSymbol(shape);
        return writer -> {
            writer.addImport(enumSymbol, enumSymbol.getName());
            writer.writeInline("$L._unknown(0)", enumSymbol.getName());
        };
    }

    @Override
    public Consumer<PythonWriter> unionShape(UnionShape shape) {
        // Streaming unions (event streams) have no synthesizable default; they also never
        // appear as dataclass properties, so missing ones don't need correction.
        if (shape.hasTrait(StreamingTrait.class)) {
            return null;
        }
        var unknownSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.UNION_UNKNOWN);
        return writer -> {
            writer.addImport(unknownSymbol, unknownSymbol.getName());
            writer.writeInline("$L(tag=\"\")", unknownSymbol.getName());
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
    @Override
    public Consumer<PythonWriter> structureShape(StructureShape shape) {
        var index = NullableIndex.of(context.model());
        for (MemberShape member : shape.members()) {
            if (!CodegenUtils.isRequiredMember(index, member)) {
                continue;
            }
            if (context.model().expectShape(member.getTarget()).accept(this) == null) {
                return null;
            }
        }
        var symbol = context.symbolProvider().toSymbol(shape);
        return writer -> {
            writer.addImport(symbol, symbol.getName());
            writer.writeInline("$L._smithy_default()", symbol.getName());
        };
    }

    @Override
    public Consumer<PythonWriter> memberShape(MemberShape shape) {
        return context.model().expectShape(shape.getTarget()).accept(this);
    }
}
