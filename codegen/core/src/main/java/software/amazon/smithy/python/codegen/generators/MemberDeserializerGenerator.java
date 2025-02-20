/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.Locale;
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
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates calls to shape serializers for member shapes.
 */
@SmithyInternalApi
public class MemberDeserializerGenerator extends ShapeVisitor.DataShapeVisitor<Void> {

    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;
    private final String deserializerName;

    public MemberDeserializerGenerator(
            GenerationContext context,
            PythonWriter writer,
            MemberShape member,
            String deserializerName
    ) {
        this.context = context;
        this.writer = writer;
        this.member = member;
        this.deserializerName = deserializerName;
    }

    private void pushMemberState() {
        pushMemberState(member);
    }

    private void pushMemberState(MemberShape member) {
        //writer.pushState();
        writer.putContext("deserializer", deserializerName);
        writer.putContext("member", member.getMemberName());
        writer.putContext("isListMember", false);
        writer.putContext("isMapMember", false);
        var parent = context.model().expectShape(member.getContainer());
        if (parent.isListShape()) {
            writer.putContext("isListMember", true);
        } else if (parent.isMapShape()) {
            writer.putContext("isMapMember", true);
        }
    }

    private void writeDeserializer(Shape shape) {
        writeDeserializer(shape.getType().name().toLowerCase(Locale.ENGLISH));
    }

    private void writeDeserializer(String shapeTypeName) {
        pushMemberState();
        writer.write(
                "${deserializer:L}.read_$L(${C|})",
                shapeTypeName,
                writer.consumer(w -> writeSchema()));
        //writer.popState();
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
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void booleanShape(BooleanShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void byteShape(ByteShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void shortShape(ShortShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void integerShape(IntegerShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void intEnumShape(IntEnumShape shape) {
        writeDeserializer("integer");
        return null;
    }

    @Override
    public Void longShape(LongShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void floatShape(FloatShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void documentShape(DocumentShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void doubleShape(DoubleShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void bigIntegerShape(BigIntegerShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void bigDecimalShape(BigDecimalShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void enumShape(EnumShape shape) {
        writeDeserializer("string");
        return null;
    }

    @Override
    public Void timestampShape(TimestampShape shape) {
        writeDeserializer(shape);
        return null;
    }

    @Override
    public Void memberShape(MemberShape shape) {
        throw new CodegenException("Unexpected shape type: Member");
    }

    @Override
    public Void listShape(ListShape shape) {
        deserializerSymbolShape(shape);
        return null;
    }

    @Override
    public Void mapShape(MapShape shape) {
        deserializerSymbolShape(shape);
        return null;
    }

    private void deserializerSymbolShape(Shape shape) {
        pushMemberState();
        var deserializerSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.DESERIALIZER);
        writer.write("$T(${deserializer:L}, ${C|})",
                deserializerSymbol,
                writer.consumer(w -> writeSchema()));
        //writer.popState();
    }

    @Override
    public Void structureShape(StructureShape shape) {
        pushMemberState();
        writer.write("$T.deserialize(${deserializer:L})", context.symbolProvider().toSymbol(shape));
        return null;
    }

    @Override
    public Void unionShape(UnionShape shape) {
        pushMemberState();
        var deserializerSymbol = context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.DESERIALIZER);
        writer.write("$T().deserialize(${deserializer:L})", deserializerSymbol);
        //writer.popState();
        return null;
    }
}
