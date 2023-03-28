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

import java.util.Collection;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.NullableIndex;
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
 * Visitor to generate deserialization functions for shapes in JSON document bodies.
 */
@SmithyUnstableApi
public class JsonShapeDeserVisitor extends ShapeVisitor.Default<Void> {
    private final GenerationContext context;
    private final PythonWriter writer;

    /**
     * Constructor.
     *
     * @param context The code generation context.
     * @param writer The writer that will be written to. Used here only to add dependencies.
     */
    public JsonShapeDeserVisitor(GenerationContext context, PythonWriter writer) {
        this.context = context;
        this.writer = writer;
    }

    private DocumentMemberDeserVisitor getMemberVisitor(MemberShape member, String dataSource) {
        return new DocumentMemberDeserVisitor(context(), writer, member, dataSource, Format.EPOCH_SECONDS);
    }

    /**
     * Gets the generation context.
     *
     * @return The generation context.
     */
    protected final GenerationContext context() {
        return context;
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
        var functionName = context.protocolGenerator().getDeserializationFunctionName(context, shape.getId());
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var symbol = context.symbolProvider().toSymbol(shape);
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document", "Document");

        var target = context.model().expectShape(shape.getMember().getTarget());
        var memberVisitor = getMemberVisitor(shape.getMember(), "e");
        var memberDeserializer = target.accept(memberVisitor);

        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-sparse-trait
        var sparseTrailer = "";
        if (shape.hasTrait(SparseTrait.class)) {
            sparseTrailer = " if e is not None else None";
        }

        writer.write("""
            def $1L(output: Document, config: $2T) -> $3T:
                if not isinstance(output, list):
                    raise $5T(f"Expected list, found {type(output)}")
                return [$4L$6L for e in output]
            """, functionName, config, symbol, memberDeserializer, errorSymbol, sparseTrailer);
        return null;
    }

    @Override
    public Void mapShape(MapShape shape) {
        var functionName = context.protocolGenerator().getDeserializationFunctionName(context, shape.getId());
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var symbol = context.symbolProvider().toSymbol(shape);
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document", "Document");

        var valueShape = context.model().expectShape(shape.getValue().getTarget());
        var valueVisitor = getMemberVisitor(shape.getValue(), "v");
        var valueDeserializer = valueShape.accept(valueVisitor);

        writer.write("""
            def $1L(output: Document, config: $2T) -> $3T:
                if not isinstance(output, dict):
                    raise $4T(f"Expected dict, found { type(output) }")
            """, functionName, config, symbol, errorSymbol);

        writer.indent();
        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-sparse-trait
        if (shape.hasTrait(SparseTrait.class)) {
            writer.write("return {k: $L if v is not None else None for k, v in output.items()}", valueDeserializer);
        } else {
            writer.write("return {k: $L for k, v in output.items() if v is not None}", valueDeserializer);
        }
        writer.dedent();
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        var functionName = context.protocolGenerator().getDeserializationFunctionName(context, shape.getId());
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var symbol = context.symbolProvider().toSymbol(shape);
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document", "Document");
        writer.write("""
            def $1L(output: Document, config: $2T) -> $3T:
                if not isinstance(output, dict):
                    raise $4T(f"Expected dict, found {type(output)}")

                kwargs: dict[str, Any] = {}

                ${5C|}

                return $3T(**kwargs)
            """, functionName, config, symbol, errorSymbol, (Runnable) () -> structureMembers(shape.members()));
        return null;
    }

    /**
     * Generate deserializers for structure members.
     *
     * <p>The structure to deserialize must exist in the variable {@literal output}, and
     * the results will be stored in a dict called {@literal kwargs}, which must also
     * exist.
     *
     * @param members The members to generate serializers for.
     */
    public void structureMembers(Collection<MemberShape> members) {
        var index = NullableIndex.of(context.model());
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        for (MemberShape member : members) {
            var pythonName = context.symbolProvider().toMemberName(member);
            var jsonName = locationName(member);

            var target = context.model().expectShape(member.getTarget());

            if (index.isMemberNullable(member)) {
                var memberVisitor = getMemberVisitor(member, "_" + pythonName);
                var memberDeserializer = target.accept(memberVisitor);
                writer.write("""
                    if (_$1L := output.get($2S)) is not None:
                        kwargs[$1S] = $3L

                    """, pythonName, jsonName, memberDeserializer);
            } else {
                var memberVisitor = getMemberVisitor(member, "output['" + jsonName + "']");
                var memberDeserializer = target.accept(memberVisitor);
                writer.write("""
                    if $2S not in output:
                        raise $4T('Expected to find $2S in the operation output, but it was not present.')
                    kwargs[$1S] = $3L

                    """, pythonName, jsonName, memberDeserializer, errorSymbol);
            }
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
    public final Void unionShape(UnionShape shape) {
        var functionName = context.protocolGenerator().getDeserializationFunctionName(context, shape.getId());
        var config = CodegenUtils.getConfigSymbol(context.settings());
        var symbol = context.symbolProvider().toSymbol(shape);
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        var unknownSymbol = symbol.expectProperty("unknown", Symbol.class);

        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document", "Document");
        writer.write("""
            def $1L(output: Document, config: $2T) -> $3T:
                if not isinstance(output, dict):
                    raise $5T(f"Expected dict, found {type(output)}")

                if (count := len(output)) != 1:
                    raise $5T(f"Unions must have exactly one member set, found {count}.")

                tag, value = list(output.items())[0]

                match tag:
                    ${6C|}

                    case _:
                        return $4T(tag)
            """, functionName, config, symbol, unknownSymbol, errorSymbol, (Runnable) () -> unionMembers(shape));
        return null;
    }

    private void unionMembers(UnionShape shape) {
        for (MemberShape member : shape.members()) {
            var jsonName = locationName(member);
            var memberSymbol = context.symbolProvider().toSymbol(member);

            var target = context.model().expectShape(member.getTarget());
            var memberVisitor = getMemberVisitor(member, "value");
            var memberDeserializer = target.accept(memberVisitor);

            writer.write("""
                case $1S:
                    return $2T($3L)

                """, jsonName, memberSymbol, memberDeserializer);
        }
    }
}
