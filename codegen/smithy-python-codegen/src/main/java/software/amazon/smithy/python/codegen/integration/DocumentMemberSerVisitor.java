/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen.integration;

import java.util.Optional;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.knowledge.HttpBinding.Location;
import software.amazon.smithy.model.knowledge.HttpBindingIndex;
import software.amazon.smithy.model.shapes.BigDecimalShape;
import software.amazon.smithy.model.shapes.BigIntegerShape;
import software.amazon.smithy.model.shapes.BlobShape;
import software.amazon.smithy.model.shapes.BooleanShape;
import software.amazon.smithy.model.shapes.ByteShape;
import software.amazon.smithy.model.shapes.DocumentShape;
import software.amazon.smithy.model.shapes.DoubleShape;
import software.amazon.smithy.model.shapes.FloatShape;
import software.amazon.smithy.model.shapes.IntegerShape;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.LongShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ResourceShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.ShortShape;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.TimestampShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Visitor to serialize member values for aggregate types into document bodies.
 *
 * <p>The standard implementations are as follows; these implementations may be
 * overridden unless otherwise specified.
 *
 * <ul>
 *   <li>Blob: base64 encoded and encoded to a utf-8 string.</li>
 *   <li>Timestamp: serialized to a string.</li>
 *   <li>Service, Operation, Resource, Member: not deserializable from documents. <b>Not overridable.</b></li>
 *   <li>List, Map, Set, Structure, Union: delegated to a serialization function.
 *     <b>Not overridable.</b></li>
 *   <li>All other types: unmodified.</li>
 * </ul>
 */
@SmithyUnstableApi
public class DocumentMemberSerVisitor implements ShapeVisitor<String> {
    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;
    private final String dataSource;
    private final Format defaultTimestampFormat;

    /**
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param member The member shape being deserialized. Used for any extra traits
     *               it might bear, such as the timestamp format.
     * @param dataSource The in-code location of the data to provide an output of
     *                   ({@code output.foo}, {@code entry}, etc.)
     * @param defaultTimestampFormat The default timestamp format used in absence
     *                               of a TimestampFormat trait.
     */
    public DocumentMemberSerVisitor(
        GenerationContext context,
        PythonWriter writer,
        MemberShape member,
        String dataSource,
        Format defaultTimestampFormat
    ) {
        this.context = context;
        this.writer = writer;
        this.member = member;
        this.dataSource = dataSource;
        this.defaultTimestampFormat = defaultTimestampFormat;
    }

    /**
     * @return the member this visitor is being run against. Used to discover member-applied
     * traits, such as @timestampFormat.
     */
    protected Optional<MemberShape> memberShape() {
        return Optional.ofNullable(member);
    }

    /**
     * Gets the generation context.
     *
     * @return The generation context.
     */
    protected final GenerationContext context() {
        return context;
    }

    /**
     * Gets the PythonWriter being written to.
     *
     * <p>This should only be used to add imports.
     *
     * @return The writer to add imports to.
     */
    protected final PythonWriter writer() {
        return writer;
    }

    /**
     * Gets the in-code location of the data to provide an output of
     * ({@code output.foo}, {@code entry}, etc.).
     *
     * @return The data source.
     */
    protected final String dataSource() {
        return dataSource;
    }

    /**
     * Gets the default timestamp format used in absence of a TimestampFormat trait.
     *
     * @return The default timestamp format.
     */
    protected final Format getDefaultTimestampFormat() {
        return defaultTimestampFormat;
    }

    @Override
    public String blobShape(BlobShape blobShape) {
        writer.addStdlibImport("base64", "b64encode");
        return String.format("b64encode(%s).decode('utf-8')", dataSource());
    }

    @Override
    public String booleanShape(BooleanShape booleanShape) {
        return dataSource();
    }

    @Override
    public String byteShape(ByteShape byteShape) {
        return dataSource();
    }

    @Override
    public String shortShape(ShortShape shortShape) {
        return dataSource();
    }

    @Override
    public String integerShape(IntegerShape integerShape) {
        return dataSource();
    }

    @Override
    public String longShape(LongShape longShape) {
        return dataSource();
    }

    @Override
    public String floatShape(FloatShape floatShape) {
        return floatShapes();
    }

    @Override
    public String documentShape(DocumentShape documentShape) {
        return dataSource();
    }

    @Override
    public String doubleShape(DoubleShape doubleShape) {
        return floatShapes();
    }

    private String floatShapes() {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "limited_serialize_float");
        return String.format("limited_serialize_float(%s)", dataSource);
    }

    @Override
    public String bigIntegerShape(BigIntegerShape bigIntegerShape) {
        return String.format("str(%s)", dataSource());
    }

    @Override
    public String bigDecimalShape(BigDecimalShape bigDecimalShape) {
        return String.format("str(%s.normalize())", dataSource());
    }

    @Override
    public final String operationShape(OperationShape shape) {
        throw new CodegenException("Operation shapes cannot be bound to documents.");
    }

    @Override
    public final String resourceShape(ResourceShape shape) {
        throw new CodegenException("Resource shapes cannot be bound to documents.");
    }

    @Override
    public final String serviceShape(ServiceShape shape) {
        throw new CodegenException("Service shapes cannot be bound to documents.");
    }

    @Override
    public final String memberShape(MemberShape shape) {
        throw new CodegenException("Member shapes cannot be bound to documents.");
    }

    @Override
    public String stringShape(StringShape stringShape) {
        return dataSource();
    }

    @Override
    public String timestampShape(TimestampShape timestampShape) {
        var sourceShape = memberShape().isPresent() ? member : timestampShape;
        var index = HttpBindingIndex.of(context.model());
        var format = index.determineTimestampFormat(sourceShape, Location.DOCUMENT, getDefaultTimestampFormat());
        return HttpProtocolGeneratorUtils.getTimestampInputParam(
            context(), writer(), dataSource(), sourceShape, format);
    }

    @Override
    public String listShape(ListShape listShape) {
        return getDelegateSerializer(listShape);
    }

    @Override
    public String mapShape(MapShape mapShape) {
        return getDelegateSerializer(mapShape);
    }

    @Override
    public String structureShape(StructureShape structureShape) {
        return getDelegateSerializer(structureShape);
    }

    @Override
    public String unionShape(UnionShape unionShape) {
        return getDelegateSerializer(unionShape);
    }

    private String getDelegateSerializer(Shape shape) {
        return getDelegateSerializer(shape, dataSource);
    }

    private String getDelegateSerializer(Shape shape, String customDataSource) {
        var serSymbol = context.protocolGenerator().getSerializationFunction(context, shape.getId());
        writer.addImport(serSymbol, serSymbol.getName());
        return serSymbol.getName() + "(" + customDataSource + ", config)";
    }
}
