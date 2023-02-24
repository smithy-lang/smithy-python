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

import java.util.Set;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.utils.SetUtils;
import software.amazon.smithy.utils.SmithyUnstableApi;


/**
 * Visitor to serialize member values for aggregate types into JSON document bodies.
 *
 * <p>This does not delegate to serializers for lists or maps that would return them
 * unchanged. A list of booleans, for example, will never need any serialization changes.
 */
@SmithyUnstableApi
public class JsonMemberSerVisitor extends DocumentMemberSerVisitor {

    private static final Set<ShapeType> NOOP_TARGETS = SetUtils.of(
        ShapeType.STRING, ShapeType.ENUM, ShapeType.BOOLEAN, ShapeType.DOCUMENT, ShapeType.BYTE, ShapeType.SHORT,
        ShapeType.INTEGER, ShapeType.INT_ENUM, ShapeType.LONG, ShapeType.FLOAT, ShapeType.DOUBLE
    );

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
    public JsonMemberSerVisitor(
        GenerationContext context,
        PythonWriter writer,
        MemberShape member,
        String dataSource,
        Format defaultTimestampFormat
    ) {
        super(context, writer, member, dataSource, defaultTimestampFormat);
    }

    @Override
    public String listShape(ListShape listShape) {
        if (isNoOpMember(listShape.getMember())) {
            return dataSource();
        }
        return super.listShape(listShape);
    }

    @Override
    public String mapShape(MapShape mapShape) {
        if (isNoOpMember(mapShape.getValue())) {
            return dataSource();
        }
        return super.mapShape(mapShape);
    }

    private boolean isNoOpMember(MemberShape member) {
        var target = context().model().expectShape(member.getTarget());
        if (target.isListShape()) {
            return isNoOpMember(target.asListShape().get().getMember());
        } else if (target.isMapShape()) {
            return isNoOpMember(target.asMapShape().get().getValue());
        }
        return NOOP_TARGETS.contains(target.getType());
    }
}
