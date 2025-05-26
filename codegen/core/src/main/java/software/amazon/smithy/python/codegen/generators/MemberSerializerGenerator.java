/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.Locale;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
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
 * Generates calls to shape serializers for member shapes.
 */
@SmithyInternalApi
public final class MemberSerializerGenerator extends ShapeVisitor.DataShapeVisitor<Void> {

    private static final Logger LOGGER = Logger.getLogger(MemberSerializerGenerator.class.getName());

    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;
    private final String serializerName;

    public MemberSerializerGenerator(
            GenerationContext context,
            PythonWriter writer,
            MemberShape member,
            String serializerName
    ) {
        this.context = context;
        this.writer = writer;
        this.member = member;
        this.serializerName = serializerName;
    }

    private void pushMemberState() {
        pushMemberState(member);
    }

    private void pushMemberState(MemberShape member) {
        writer.pushState();
        writer.putContext("serializer", serializerName);
        writer.putContext("member", member.getMemberName());
        writer.putContext("isListMember", false);
        writer.putContext("isMapMember", false);
        var parent = context.model().expectShape(member.getContainer());
        if (parent.isUnionShape()) {
            writer.putContext("property", "self.value");
        } else if (parent.isListShape()) {
            writer.putContext("property", "e");
            writer.putContext("isListMember", true);
        } else if (parent.isMapShape()) {
            writer.putContext("property", "v");
            writer.putContext("isMapMember", true);
        } else {
            writer.putContext("property", "self." + context.symbolProvider().toMemberName(member));
        }
    }

    private void writeSerializer(Shape shape) {
        writeSerializer(shape.getType().name().toLowerCase(Locale.ENGLISH));
    }

    private void writeSerializer(String typeName) {
        pushMemberState();
        writer.write("${serializer:L}.write_$L(${C|}, ${property:L})", typeName, writer.consumer(w -> writeSchema()));
        writer.popState();

    }

    private void writeSchema() {
        var parent = context.model().expectShape(member.getContainer());
        if (parent.isListShape()) {
            writer.writeInline("member_schema");
        } else if (parent.isMapShape()) {
            writer.writeInline("value_schema");
        } else {
            writer.writeInline("${schema:T}.members[${member:S}]");
        }
    }

    @Override
    public Void blobShape(BlobShape shape) {
        if (shape.hasTrait(StreamingTrait.class)) {
            writeSerializer("data_stream");
        } else {
            writeSerializer(shape);
        }
        return null;
    }

    @Override
    public Void booleanShape(BooleanShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void byteShape(ByteShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void shortShape(ShortShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void integerShape(IntegerShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void intEnumShape(IntEnumShape shape) {
        writeSerializer("integer");
        return null;
    }

    @Override
    public Void longShape(LongShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void floatShape(FloatShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void documentShape(DocumentShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void doubleShape(DoubleShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void bigIntegerShape(BigIntegerShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void bigDecimalShape(BigDecimalShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void enumShape(EnumShape shape) {
        writeSerializer("string");
        return null;
    }

    @Override
    public Void memberShape(MemberShape shape) {
        pushMemberState();
        throw new CodegenException("Unexpected shape type: Member");
    }

    @Override
    public Void timestampShape(TimestampShape shape) {
        writeSerializer(shape);
        return null;
    }

    @Override
    public Void listShape(ListShape shape) {
        pushMemberState();
        var serializerSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.SERIALIZER);
        writer.write("$T(${serializer:L}, ${C|}, ${property:L})",
                serializerSymbol,
                writer.consumer(w -> writeSchema()));
        writer.popState();
        return null;
    }

    @Override
    public Void mapShape(MapShape shape) {
        pushMemberState();
        var serializerSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.SERIALIZER);
        writer.write("$T(${serializer:L}, ${C|}, ${property:L})",
                serializerSymbol,
                writer.consumer(w -> writeSchema()));
        writer.popState();
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        writeSerializer("struct");
        return null;
    }

    @Override
    public Void unionShape(UnionShape shape) {
        writeSerializer("struct");
        return null;
    }
}
