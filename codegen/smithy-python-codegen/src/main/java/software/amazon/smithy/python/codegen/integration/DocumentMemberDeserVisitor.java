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
 * Visitor to generate member values for aggregate types deserialized from documents.
 *
 * <p>The standard implementations are as follows; these implementations may be
 * overridden unless otherwise specified.
 *
 * <ul>
 *   <li>Blob: base64 decoded.</li>
 *   <li>BigDecimal: converted to decimal.Decimal.</li>
 *   <li>Timestamp: converted to datetime.datetime in UTC.</li>
 *   <li>Service, Operation, Resource, Member: not deserializable from documents. <b>Not overridable.</b></li>
 *   <li>Document, List, Map, Set, Structure, Union: delegated to a deserialization function.
 *     <b>Not overridable.</b></li>
 *   <li>All other types: unmodified.</li>
 * </ul>
 */
@SmithyUnstableApi
public class DocumentMemberDeserVisitor implements ShapeVisitor<String> {
    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;
    private final String dataSource;
    private final Format defaultTimestampFormat;

    /**
     * Constructor.
     *
     * @param context The generation context.
     * @param writer The writer being written to, used for adding imports.
     * @param dataSource The in-code location of the data to provide an output of
     *                   ({@code output.foo}, {@code entry}, etc.)
     * @param defaultTimestampFormat The default timestamp format used in absence
     *                               of a TimestampFormat trait.
     */
    public DocumentMemberDeserVisitor(
        GenerationContext context,
        PythonWriter writer,
        String dataSource,
        Format defaultTimestampFormat
    ) {
        this(context, writer, null, dataSource, defaultTimestampFormat);
    }

    /**
     * Constructor.
     *
     * @param context The generation context.
     * @param writer The writer being written to, used for adding imports.
     * @param member The member shape being deserialized. Used for any extra traits
     *               it might bear, such as the timestamp format.
     * @param dataSource The in-code location of the data to provide an output of
     *                   ({@code output.foo}, {@code entry}, etc.)
     * @param defaultTimestampFormat The default timestamp format used in absence
     *                               of a TimestampFormat trait.
     */
    public DocumentMemberDeserVisitor(
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
    public String blobShape(BlobShape shape) {
        writer.addStdlibImport("base64", "b64decode");
        writer.addImport("smithy_python.utils", "expect_type");
        return "b64decode(expect_type(str, " + dataSource + "))";
    }

    @Override
    public String booleanShape(BooleanShape shape) {
        writer.addImport("smithy_python.utils", "expect_type");
        return "expect_type(bool, " + dataSource + ")";
    }

    @Override
    public String byteShape(ByteShape shape) {
        // TODO: add bounds checks
        return intShape();
    }

    @Override
    public String shortShape(ShortShape shape) {
        // TODO: add bounds checks
        return intShape();
    }

    @Override
    public String integerShape(IntegerShape shape) {
        // TODO: add bounds checks
        return intShape();
    }

    @Override
    public String longShape(LongShape shape) {
        // TODO: add bounds checks
        return intShape();
    }

    private String intShape() {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "expect_type");
        return "expect_type(int, " + dataSource + ")";
    }

    @Override
    public String floatShape(FloatShape shape) {
        // TODO: perform a bounds check
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "limited_parse_float");
        return "limited_parse_float(" + dataSource + ")";
    }

    @Override
    public String doubleShape(DoubleShape shape) {
        // TODO: perform a bounds check
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "limited_parse_float");
        return "limited_parse_float(" + dataSource + ")";
    }

    @Override
    public String stringShape(StringShape shape) {
        // TODO: handle strings with media types
        writer.addImport("smithy_python.utils", "expect_type");
        return "expect_type(str, " + dataSource + ")";
    }

    @Override
    public String bigIntegerShape(BigIntegerShape shape) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "expect_type");
        return "expect_type(int, " + dataSource + ")";
    }

    @Override
    public String bigDecimalShape(BigDecimalShape shape) {
        writer.addStdlibImport("decimal", "Decimal", "_Decimal");
        writer.addImport("smithy_python.utils", "expect_type");
        return "_Decimal(expect_type(str" + dataSource + "))";
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
    public String timestampShape(TimestampShape shape) {
        var httpIndex = HttpBindingIndex.of(context.model());
        Format format;
        if (memberShape().isEmpty()) {
            format = httpIndex.determineTimestampFormat(shape, Location.DOCUMENT, defaultTimestampFormat);
        } else {
            var member = memberShape().get();
            if (!shape.getId().equals(member.getTarget())) {
                throw new CodegenException(
                    String.format("Encountered timestamp shape %s that was not the target of member shape %s",
                        shape.getId(), member.getId()));
            }
            format = httpIndex.determineTimestampFormat(member, Location.DOCUMENT, defaultTimestampFormat);
        }

        return HttpProtocolGeneratorUtils.getTimestampOutputParam(writer, dataSource, shape, format);
    }

    @Override
    public final String documentShape(DocumentShape shape) {
        return dataSource();
    }

    @Override
    public final String listShape(ListShape shape) {
        return getDelegateDeserializer(shape);
    }

    @Override
    public final String mapShape(MapShape shape) {
        return getDelegateDeserializer(shape);
    }

    @Override
    public final String structureShape(StructureShape shape) {
        return getDelegateDeserializer(shape);
    }

    @Override
    public final String unionShape(UnionShape shape) {
        return getDelegateDeserializer(shape);
    }

    private String getDelegateDeserializer(Shape shape) {
        return getDelegateDeserializer(shape, dataSource);
    }

    private String getDelegateDeserializer(Shape shape, String customDataSource) {
        var deserSymbol = context.protocolGenerator().getDeserializationFunction(context, shape.getId());
        writer.addImport(deserSymbol, deserSymbol.getName());
        return deserSymbol.getName() + "(" + customDataSource + ", config)";
    }
}
