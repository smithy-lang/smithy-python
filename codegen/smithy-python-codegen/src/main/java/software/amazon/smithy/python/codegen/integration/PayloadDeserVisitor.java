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
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Visitor to generate deserialization functions for shapes marked as HttpPayloads.
 */
@SmithyUnstableApi
public class PayloadDeserVisitor extends ShapeVisitor.Default<Void> {

    private final GenerationContext context;
    private final PythonWriter writer;
    private final MemberShape member;

    public PayloadDeserVisitor(GenerationContext context, PythonWriter writer, HttpBinding binding) {
        this.context = context;
        this.writer = writer;
        this.member = binding.getMember();
    }

    @Override
    protected Void getDefault(Shape shape) {
        throw new CodegenException(
            "Shape type " + shape.getType() + " of shape " + shape + " is not a supported httpPayload."
        );
    }

    @Override
    public Void blobShape(BlobShape shape) {
        if (member.getMemberTrait(context.model(), StreamingTrait.class).isPresent()) {
            writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
            writer.write("kwargs[$S] = AsyncBytesReader(http_response.body)",
                CaseUtils.toSnakeCase(member.getMemberName()));
        } else {
            writer.write("""
                if (body := await http_response.consume_body()):
                    kwargs[$1S] = body

                """, CaseUtils.toSnakeCase(member.getMemberName()));
        }

        return null;
    }

    @Override
    public Void stringShape(StringShape shape) {
        writer.write("""
            if (body := await http_response.consume_body()):
                kwargs[$S] = body.decode()

            """, CaseUtils.toSnakeCase(member.getMemberName()));
        return null;
    }

    @Override
    public Void structureShape(StructureShape shape) {
        writer.addStdlibImport("json", "loads", "json_loads");

        // TODO: its possible that the function here has not been initialized.
        //  How to prevent naming conflicts without having potentially uninitialized function?
        writer.write("""
                if (body := await http_response.consume_body()):
                    kwargs[$S] = $L(json_loads(body), config)

                """,
            CaseUtils.toSnakeCase(member.getMemberName()),
            context.protocolGenerator().getDeserializationFunctionName(context, shape.getId())
        );

        return null;
    }

    @Override
    public Void documentShape(DocumentShape shape) {
        writer.addStdlibImport("json", "loads", "json_loads");
        writer.write("""
            if (body := await http_response.consume_body()):
                kwargs[$S] = json_loads(body)

            """, CaseUtils.toSnakeCase(member.getMemberName()));
        return null;
    }
}
