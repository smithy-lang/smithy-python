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

import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.shapes.BlobShape;
import software.amazon.smithy.model.shapes.DocumentShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;


/**
 * Visitor to generate deserialization functions for shapes marked as HttpPayloads.
 */
@SmithyUnstableApi
public final class JsonPayloadDeserVisitor extends ShapeVisitor.Default<Void> {
    private static final Format DEFAULT_EPOCH_FORMAT = Format.EPOCH_SECONDS;

    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;

    public JsonPayloadDeserVisitor(GenerationContext context, PythonWriter writer, HttpBinding binding) {
        this.context = context;
        this.writer = writer;
        this.member = binding.getMember();
    }

    private DocumentMemberDeserVisitor getMemberVisitor(MemberShape member, String dataSource) {
        return new DocumentMemberDeserVisitor(context, writer, member, dataSource, DEFAULT_EPOCH_FORMAT);
    }

    protected Void getDefault(Shape shape) {
        throw new CodegenException(
            "Shape " + shape + " of type " + shape.getType() + " is not supported as an httpPayload."
        );
    }

    @Override
    public Void blobShape(BlobShape shape) {
        // see: https://smithy.io/2.0/spec/streaming.html#smithy-api-streaming-trait
        if (member.getMemberTrait(context.model(), StreamingTrait.class).isPresent()) {
            writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
            writer.write("kwargs[$S] = AsyncBytesReader(http_response.body)",
                context.symbolProvider().toMemberName(member));
        } else {
            writer.write("""
                    if (body := await http_response.consume_body()):
                        kwargs[$1S] = body

                    """,
                context.symbolProvider().toMemberName(member)
            );
        }

        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        writer.write("""
                if (body := await http_response.consume_body()):
                    kwargs[$S] = body.decode('utf-8')

                """,
            context.symbolProvider().toMemberName(member)
        );

        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        generateJsonDeserializerDelegation();
        return null;
    }

    @Override
    public Void unionShape(UnionShape shape) {
        generateJsonDeserializerDelegation();
        return null;
    }

    @Override
    public Void documentShape(DocumentShape shape) {
        generateJsonDeserializerDelegation();
        return null;
    }

    private void generateJsonDeserializerDelegation() {
        writer.addStdlibImport("json");

        var target = context.model().expectShape(member.getTarget());
        var memberVisitor = getMemberVisitor(member, "json.loads(body)");
        var memberDeserializer = target.accept(memberVisitor);

        writer.write("""
                if (body := await http_response.consume_body()):
                    kwargs[$S] = $L

                """,
            context.symbolProvider().toMemberName(member),
            memberDeserializer
        );
    }
}
