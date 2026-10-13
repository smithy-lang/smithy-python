/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Shared base for the member serializer and deserializer generators, holding the
 * schema-location logic that is identical between the two directions.
 */
@SmithyInternalApi
abstract class AbstractMemberGenerator extends ShapeVisitor.DataShapeVisitor<Void> {

    protected final GenerationContext context;
    protected final PythonWriter writer;
    protected final MemberShape member;

    AbstractMemberGenerator(GenerationContext context, PythonWriter writer, MemberShape member) {
        this.context = context;
        this.writer = writer;
        this.member = member;
    }

    /** A list/map member reaches its schema through the container's element schema. */
    protected void writeSchema() {
        var parent = context.model().expectShape(member.getContainer());
        if (parent.isListShape()) {
            writer.writeInline("member_schema");
        } else if (parent.isMapShape()) {
            writer.writeInline("value_schema");
        } else {
            writer.writeInline("members[$L]", Integer.toString(memberIndex(parent)));
        }
    }

    protected int memberIndex(Shape parent) {
        int index = 0;
        for (var m : parent.members()) {
            if (m.getMemberName().equals(member.getMemberName())) {
                return index;
            }
            index++;
        }
        throw new CodegenException("Member not found in container: " + member.getId());
    }
}
