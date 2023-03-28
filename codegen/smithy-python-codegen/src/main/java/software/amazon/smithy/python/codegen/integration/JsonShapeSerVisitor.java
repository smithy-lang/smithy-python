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

import java.util.Collection;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ResourceShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.JsonNameTrait;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Visitor to generate serialization functions for shapes in JSON document bodies.
 */
@SmithyUnstableApi
public class JsonShapeSerVisitor extends ShapeVisitor.Default<Void> {
    private final GenerationContext context;
    private final PythonWriter writer;

    /**
     * Constructor.
     *
     * @param context The code generation context.
     * @param writer The writer that will be written to. Used here only to add dependencies.
     */
    public JsonShapeSerVisitor(GenerationContext context, PythonWriter writer) {
        this.context = context;
        this.writer = writer;
    }

    /**
     * Gets the serialization visitor for a member.
     *
     * @param member The member to be serialized.
     * @param dataSource The python variable / source containing the data to serialize.
     * @return The serialization visitor for the member.
     */
    protected DocumentMemberSerVisitor getMemberVisitor(MemberShape member, String dataSource) {
        return new JsonMemberSerVisitor(context, writer, member, dataSource, Format.EPOCH_SECONDS);
    }

    @Override
    protected Void getDefault(Shape shape) {
        return null;
    }

    @Override
    public final Void operationShape(OperationShape shape) {
        throw new CodegenException("Operation shapes cannot be bound to documents.");
    }

    @Override
    public final Void resourceShape(ResourceShape shape) {
        throw new CodegenException("Resource shapes cannot be bound to documents.");
    }

    @Override
    public final Void serviceShape(ServiceShape shape) {
        throw new CodegenException("Service shapes cannot be bound to documents.");
    }

    @Override
    public Void listShape(ListShape shape) {
        var functionName = context.protocolGenerator().getSerializationFunctionName(context, shape);
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var listSymbol = context.symbolProvider().toSymbol(shape);

        var target = context.model().expectShape(shape.getMember().getTarget());
        var memberVisitor = getMemberVisitor(shape.getMember(), "e");
        var memberSerializer = target.accept(memberVisitor);

        // If we're not doing a transform, there's no need to have a function for it.
        if (memberSerializer.equals("e")) {
            return null;
        }

        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-sparse-trait
        var sparseTrailer = "";
        if (shape.hasTrait(SparseTrait.class)) {
            sparseTrailer = " if e is not None else None";
        }

        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.write("""
            def $1L(input: $2T, config: $3T) -> list[Document]:
                return [$4L$5L for e in input]
            """, functionName, listSymbol, config, memberSerializer, sparseTrailer);
        return null;
    }

    @Override
    public Void mapShape(MapShape shape) {
        var functionName = context.protocolGenerator().getSerializationFunctionName(context, shape);
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var mapSymbol = context.symbolProvider().toSymbol(shape);

        var target = context.model().expectShape(shape.getValue().getTarget());
        var valueVisitor = getMemberVisitor(shape.getValue(), "v");
        var valueSerializer = target.accept(valueVisitor);

        // If we're not doing a transform, there's no need to have a function for it.
        if (valueSerializer.equals("v")) {
            return null;
        }

        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-sparse-trait
        var sparseTrailer = "";
        if (shape.hasTrait(SparseTrait.class)) {
            sparseTrailer = " if v is not None else None";
        }

        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.write("""
            def $1L(input: $2T, config: $3T) -> dict[str, Document]:
                return {k: $4L$5L for k, v in input.items()}
            """, functionName, mapSymbol, config, valueSerializer, sparseTrailer);
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        var functionName = context.protocolGenerator().getSerializationFunctionName(context, shape);
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var structureSymbol = context.symbolProvider().toSymbol(shape);
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");

        writer.write("""
            def $1L(input: $2T, config: $3T) -> dict[str, Document]:
                result: dict[str, Document] = {}

                ${4C|}
                return result
            """, functionName, structureSymbol, config, (Runnable) () -> structureMembers(shape.members()));
        return null;
    }

    /**
     * Generate serializers for structure members.
     *
     * <p>The structure to serialize must exist in the variable {@literal input}, and
     * the output will be stored in a dict called {@literal result}, which must also
     * exist.
     *
     * @param members The members to generate serializers for.
     */
    public void structureMembers(Collection<MemberShape> members) {
        for (MemberShape member : members) {
            var pythonName = context.symbolProvider().toMemberName(member);
            var jsonName = locationName(member);
            var target = context.model().expectShape(member.getTarget());

            var memberVisitor = getMemberVisitor(member, "input." + pythonName);
            var memberSerializer = target.accept(memberVisitor);

            CodegenUtils.accessStructureMember(context, writer, "input", member, () -> {
                writer.write("result[$S] = $L\n", jsonName, memberSerializer);
            });
        }
    }

    /**
     * Gets the JSON key that will be used for a given member.
     *
     * @param member The member to inspect.
     * @return The string key that will be used for the member.
     */
    protected String locationName(MemberShape member) {
        // see: https://smithy.io/2.0/spec/protocol-traits.html#smithy-api-jsonname-trait
        return member.getMemberTrait(context.model(), JsonNameTrait.class)
            .map(StringTrait::getValue)
            .orElse(member.getMemberName());
    }

    @Override
    public Void unionShape(UnionShape shape) {
        var functionName = context.protocolGenerator().getSerializationFunctionName(context, shape);
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var unionSymbol = context.symbolProvider().toSymbol(shape);
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");

        writer.write("""
            def $1L(input: $2T, config: $3T) -> dict[str, Document]:
                match input:
                    ${5C|}
                    case _:
                        raise $4T(f"Unexpected union variant: {type(input)}")
            """, functionName, unionSymbol, config, errorSymbol, (Runnable) () -> unionMembers(shape.members()));
        return null;
    }

    private void unionMembers(Collection<MemberShape> members) {
        for (MemberShape member : members) {
            var jsonName = locationName(member);
            var memberSymbol = context.symbolProvider().toSymbol(member);
            var target = context.model().expectShape(member.getTarget());
            var memberVisitor = getMemberVisitor(member, "input.value");
            var memberSerializer = target.accept(memberVisitor);

            writer.write("""
                case $T():
                    return {$S: $L}
                """, memberSymbol, jsonName, memberSerializer);
        }
    }
}
