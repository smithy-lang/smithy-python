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

import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;
import software.amazon.smithy.aws.traits.protocols.RestJson1Trait;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.knowledge.NeighborProviderIndex;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.RequiresLengthTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Abstract implementation of JSON-based protocols that use REST bindings.
 *
 * <p>This class will be capable of generating a functional protocol based on
 * the semantics of Amazon's RestJson1 protocol. Extension hooks will be
 * provided where necessary in the few cases where that protocol uses
 * Amazon-specific terminology or functionality.
 */
@SmithyUnstableApi
public class RestJsonProtocolGenerator extends HttpBindingProtocolGenerator {

    private static final Set<String> TESTS_TO_SKIP = Set.of(
        // These two tests essentially try to assert nan == nan,
        // which is never true. We should update the generator to
        // make specific assertions for these.
        "RestJsonSupportsNaNFloatHeaderOutputs",
        "RestJsonSupportsNaNFloatInputs",

        // This requires support of idempotency autofill
        "RestJsonQueryIdempotencyTokenAutoFill",

        // This requires support of the httpChecksumRequired trait
        "RestJsonHttpChecksumRequired",

        // These require support of the endpoint trait
        "RestJsonEndpointTraitWithHostLabel",
        "RestJsonEndpointTrait",

        // TODO: support the request compression trait
        // https://smithy.io/2.0/spec/behavior-traits.html#smithy-api-requestcompression-trait
        "SDKAppliedContentEncoding_restJson1",
        "SDKAppendedGzipAfterProvidedEncoding_restJson1"
    );

    @Override
    public ShapeId getProtocol() {
        return RestJson1Trait.ID;
    }

    @Override
    protected Format getDocumentTimestampFormat() {
        return Format.EPOCH_SECONDS;
    }

    @Override
    protected String getDocumentContentType() {
        return "application/json";
    }

    // This is here rather than in HttpBindingProtocolGenerator because eventually
    // it will need to generate some protocol-specific comparators.
    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator().useFileWriter("./tests/test_protocol.py", "tests.test_protocol", writer -> {
            new HttpProtocolTestGenerator(
                context, getProtocol(), writer, (shape, testCase) -> filterTests(testCase)
            ).run();
        });
    }

    private boolean filterTests(HttpMessageTestCase testCase) {
        return TESTS_TO_SKIP.contains(testCase.getId());
    }

    @Override
    protected void serializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.write("result: dict[str, Document] = {}\n");

        var bodyMembers = documentBindings.stream()
            .map(HttpBinding::getMember)
            .collect(Collectors.toSet());

        var serVisitor = new JsonShapeSerVisitor(context, writer);
        serVisitor.structureMembers(bodyMembers);

        writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
        writer.addStdlibImport("json");

        var defaultTrailer = shouldWriteDefaultBody(context, operation) ? "" : " if result else b''";
        writer.write("""
            content = json.dumps(result).encode('utf-8')$L
            content_length = len(content)
            body = AsyncBytesReader(content)
            """, defaultTrailer);
    }

    @Override
    protected void serializePayloadBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBinding payloadBinding
    ) {
        var target = context.model().expectShape(payloadBinding.getMember().getTarget());
        var dataSource = "input." + context.symbolProvider().toMemberName(payloadBinding.getMember());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);

        // The streaming trait can either be bound to a union, meaning it's an event stream,
        // or a blob, meaning it's some potentially big collection of bytes.
        // See also: https://smithy.io/2.0/spec/streaming.html#smithy-api-streaming-trait
        if (payloadBinding.getMember().getMemberTrait(context.model(), StreamingTrait.class).isPresent()) {
            // TODO: support event streams
            if (target.isUnionShape()) {
                return;
            }

            // If the stream requires a length, we need to calculate that. We can't initialize the
            // variable in the property accessor because then it would be out of scope, so we do
            // it here instead.
            // See also https://smithy.io/2.0/spec/streaming.html#smithy-api-requireslength-trait
            if (requiresLength(context, payloadBinding.getMember())) {
                writer.write("content_length: int = 0");
            }

            CodegenUtils.accessStructureMember(context, writer, "input", payloadBinding.getMember(), () -> {
                if (requiresLength(context, payloadBinding.getMember())) {
                    // Since we need to calculate the length, we need to use a seekable stream because
                    // we can't assume that the source is seekable or safe to read more than once.
                    writer.addImport("smithy_python.interfaces.blobs", "SeekableAsyncBytesReader");
                    writer.write("""
                        body = SeekableAsyncBytesReader($L)
                        await body.seek(0, 2)
                        content_length = body.tell()
                        await body.seek(0, 0)
                        """, dataSource);
                } else {
                    writer.addStdlibImport("typing", "AsyncIterator");
                    writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
                    writer.write("""
                        if isinstance($1L, AsyncIterator):
                            body = $1L
                        else:
                            body = AsyncBytesReader($1L)
                        """, dataSource);
                }
            });
            return;
        }

        var memberVisitor = new JsonMemberSerVisitor(
            context, writer, payloadBinding.getMember(), dataSource, Format.EPOCH_SECONDS);
        var memberSerializer = target.accept(memberVisitor);
        writer.addImport("smithy_python.interfaces.blobs", "AsyncBytesReader");
        writer.write("content_length: int = 0");

        CodegenUtils.accessStructureMember(context, writer, "input", payloadBinding.getMember(), () -> {
            if (target.isBlobShape()) {
                writer.write("content_length = len($L)", dataSource);
                writer.write("body = AsyncBytesReader($L)", dataSource);
                return;
            }

            if (target.isStringShape()) {
                writer.write("content = $L.encode('utf-8')", memberSerializer);
            } else {
                writer.write("content = json.dumps($L).encode('utf-8')", memberSerializer);
            }
            writer.write("content_length = len(content)");
            writer.write("body = AsyncBytesReader(content)");
        });
        if (target.isStructureShape()) {
            writer.write("""
                else:
                    content_length = 2
                    body = AsyncBytesReader(b'{}')
                """);
        }
    }

    private boolean requiresLength(GenerationContext context, MemberShape member) {
        // see: https://smithy.io/2.0/spec/streaming.html#smithy-api-requireslength-trait
        return member.getMemberTrait(context.model(), RequiresLengthTrait.class).isPresent();
    }

    @Override
    protected void generateDocumentBodyShapeSerializers(GenerationContext context, Set<Shape> shapes) {
        for (Shape shape : getConnectedShapes(context, shapes)) {
            var serFunction = context.protocolGenerator().getSerializationFunction(context, shape);
            context.writerDelegator().useFileWriter(serFunction.getDefinitionFile(),
                serFunction.getNamespace(), writer -> {
                    shape.accept(new JsonShapeSerVisitor(context, writer));
                });
        }
    }

    @Override
    protected void deserializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.addStdlibImport("json");

        if (operationOrError.isOperationShape()) {
            writer.write("""
                output: dict[str, Document] = {}
                if (body := await http_response.consume_body()):
                    output = json.loads(body)

                """);
        } else {
            // The method that parses the error code will also pre-parse the body if there are no errors
            // on that operation with an http payload. If the operation has at least 1 error with an
            // http payload then the body cannot be safely pre-parsed and must be parsed here
            // within the deserializer
            writer.addStdlibImport("typing", "cast");
            writer.write("""
                if (parsed_body is None) and (body := await http_response.consume_body()):
                    parsed_body = json.loads(body)

                output: dict[str, Document] = parsed_body if parsed_body is not None else {}
                """);
        }

        var bodyMembers = documentBindings.stream()
            .map(HttpBinding::getMember)
            .collect(Collectors.toSet());

        var deserVisitor = new JsonShapeDeserVisitor(context, writer);
        deserVisitor.structureMembers(bodyMembers);
    }

    @Override
    protected void generateDocumentBodyShapeDeserializers(
        GenerationContext context,
        Set<Shape> shapes
    ) {
        for (Shape shape : getConnectedShapes(context, shapes)) {
            var deserFunction = context.protocolGenerator().getDeserializationFunction(context, shape);

            context.writerDelegator().useFileWriter(deserFunction.getDefinitionFile(),
                    deserFunction.getNamespace(), writer -> {
                shape.accept(new JsonShapeDeserVisitor(context, writer));
            });
        }
    }

    @Override
    protected void deserializePayloadBody(GenerationContext context,
                                          PythonWriter writer,
                                          Shape operationOrError,
                                          HttpBinding payloadBinding
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        var visitor = new JsonPayloadDeserVisitor(context, writer, payloadBinding);
        var target = context.model().expectShape(payloadBinding.getMember().getTarget());
        target.accept(visitor);
    }

    private Set<Shape> getConnectedShapes(GenerationContext context, Set<Shape> initialShapes) {
        var shapeWalker = new Walker(NeighborProviderIndex.of(context.model()).getProvider());
        var connectedShapes = new TreeSet<>(initialShapes);
        initialShapes.forEach(shape -> connectedShapes.addAll(shapeWalker.walkShapes(shape)));
        return connectedShapes;
    }

    @Override
    protected void resolveErrorCodeAndMessage(GenerationContext context,
                                              PythonWriter writer,
                                              Boolean canReadResponseBody
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.protocolutils", "parse_rest_json_error_info");
        writer.writeInline("code, message, parsed_body = await parse_rest_json_error_info(http_response");
        if (!canReadResponseBody) {
            writer.writeInline(", False");
        }
        writer.write(")");
    }
}
