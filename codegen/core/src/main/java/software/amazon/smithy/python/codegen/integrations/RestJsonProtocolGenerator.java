/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.RestJson1Trait;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.RequiresLengthTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
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
            "SDKAppendedGzipAfterProvidedEncoding_restJson1",

            // TODO: update union deserialization to ignore `__type` for JSON protocols
            "RestJsonDeserializeIgnoreType",

            // These tests do need to be fixed, but they're being disabled right now
            // since the way protocols work is changing.
            "RestJsonClientPopulatesDefaultValuesInInput",
            "RestJsonClientSkipsTopLevelDefaultValuesInInput",
            "RestJsonClientUsesExplicitlyProvidedMemberValuesOverDefaults",
            "RestJsonClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
            "RestJsonClientPopulatesDefaultsValuesWhenMissingInResponse",
            "RestJsonClientIgnoresDefaultValuesIfMemberValuesArePresentInResponse",
            "RestJsonClientPopulatesNestedDefaultsWhenMissingInResponseBody",
            "RestJsonHttpPrefixEmptyHeaders",
            "RestJsonNullAndEmptyHeaders",
            "HttpPrefixEmptyHeaders");

    @Override
    public ShapeId getProtocol() {
        return RestJson1Trait.ID;
    }

    @Override
    public ApplicationProtocol getApplicationProtocol(GenerationContext context) {
        var service = context.settings().service(context.model());
        var trait = service.expectTrait(RestJson1Trait.class);
        var config = ObjectNode.builder()
                .withMember("http", ArrayNode.fromStrings(trait.getHttp()))
                .withMember("eventStreamHttp", ArrayNode.fromStrings(trait.getEventStreamHttp()))
                .build();
        return ApplicationProtocol.createDefaultHttpApplicationProtocol(config);
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
                    context,
                    getProtocol(),
                    writer,
                    (shape, testCase) -> filterTests(testCase)).run();
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
        writer.addDependency(SmithyPythonDependency.SMITHY_JSON);
        writer.addImport("smithy_json", "JSONCodec");
        writer.addImport("smithy_core.aio.types", "SeekableAsyncBytesReader");

        writer.pushState();

        if (documentBindings.isEmpty()) {
            var body = shouldWriteDefaultBody(context, operation) ? "b\"{}\"" : "b\"\"";
            writer.write("""
                    content_length = 0
                    body = SeekableAsyncBytesReader($L)
                    """, body);
        } else {
            writer.addImport("smithy_core.types", "TimestampFormat");
            writer.putContext("writeDefaultBody", shouldWriteDefaultBody(context, operation));
            writer.write("""
                    codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                    content = codec.serialize(input)
                    ${?writeDefaultBody}
                    if not content:
                        content = b\"{}\"
                    ${/writeDefaultBody}
                    content_length = len(content)
                    body = SeekableAsyncBytesReader(content)
                    """);
        }

        writer.popState();
    }

    @Override
    protected void writeDefaultHeaders(GenerationContext context, PythonWriter writer, OperationShape operation) {
        var eventStreamIndex = EventStreamIndex.of(context.model());
        if (eventStreamIndex.getInputInfo(operation).isPresent()) {
            writer.addImport("smithy_http", "Field");
            writer.write(
                    "Field(name=\"Content-Type\", values=[$S]),",
                    "application/vnd.amazon.eventstream");
            writer.write(
                    "Field(name=\"X-Amz-Content-SHA256\", values=[$S]),",
                    "STREAMING-AWS4-HMAC-SHA256-EVENTS");
        }
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
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

        // The streaming trait can either be bound to a union, meaning it's an event stream,
        // or a blob, meaning it's some potentially big collection of bytes.
        // See also: https://smithy.io/2.0/spec/streaming.html#smithy-api-streaming-trait
        if (payloadBinding.getMember().getMemberTrait(context.model(), StreamingTrait.class).isPresent()) {
            if (target.isUnionShape()) {
                writer.addImport("smithy_core.aio.types", "AsyncBytesProvider");
                writer.write("body = AsyncBytesProvider()");
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
                    writer.addImport("smithy_core.aio.types", "SeekableAsyncBytesReader");
                    writer.write("""
                            body = SeekableAsyncBytesReader($L)
                            await body.seek(0, 2)
                            content_length = body.tell()
                            await body.seek(0, 0)
                            """, dataSource);
                } else {
                    writer.addStdlibImport("typing", "AsyncIterator");
                    writer.addImport("smithy_core.aio.types", "AsyncBytesReader");
                    // Note that this type ignore is because we can't explicitly narrow the iterator to
                    // a bytes iterator and pyright isn't quite as clever about narrowing the union as
                    // mypy is in this case.
                    writer.write("""
                            if isinstance($1L, AsyncIterator):
                                body = $1L  # type: ignore
                            else:
                                body = AsyncBytesReader($1L)
                            """, dataSource);
                }
            });
            return;
        }

        writer.addImport("smithy_core.aio.types", "SeekableAsyncBytesReader");
        writer.write("content_length: int = 0");

        CodegenUtils.accessStructureMember(context, writer, "input", payloadBinding.getMember(), () -> {
            if (target.isBlobShape()) {
                writer.write("content_length = len($L)", dataSource);
                writer.write("body = SeekableAsyncBytesReader($L)", dataSource);
                return;
            }

            if (target.isStringShape()) {
                writer.write("content = $L.encode('utf-8')", dataSource);
            } else {
                writer.addImport("smithy_json", "JSONCodec");
                writer.addImport("smithy_core.types", "TimestampFormat");
                writer.write("""
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        content = codec.serialize($L)
                        """, dataSource);
            }
            writer.write("content_length = len(content)");
            writer.write("body = SeekableAsyncBytesReader(content)");
        });
        if (target.isStructureShape()) {
            writer.write("""
                    else:
                        content_length = 2
                        body = SeekableAsyncBytesReader(b\"{}\")
                    """);
        }
    }

    private boolean requiresLength(GenerationContext context, MemberShape member) {
        // see: https://smithy.io/2.0/spec/streaming.html#smithy-api-requireslength-trait
        return member.getMemberTrait(context.model(), RequiresLengthTrait.class).isPresent();
    }

    @Override
    protected void generateDocumentBodyShapeSerializers(GenerationContext context, Set<Shape> shapes) {
        // No longer needed now that JSONCodec is handling it
    }

    @Override
    protected void deserializeDocumentBody(
            GenerationContext context,
            PythonWriter writer,
            Shape operationOrError,
            List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_JSON);
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addImport("smithy_json", "JSONCodec");
        writer.addImport("smithy_core.types", "TimestampFormat");

        var symbolProvider = context.symbolProvider();
        var symbol = symbolProvider.toSymbol(operationOrError);
        if (operationOrError.isOperationShape()) {
            var output = context.model().expectShape(operationOrError.asOperationShape().get().getOutputShape());
            symbol = symbolProvider.toSymbol(output);
        }

        if (operationOrError.isOperationShape()) {
            writer.write("body = await http_response.consume_body_async()");
        } else {
            // TODO extract error codes in another way
            writer.addStdlibImport("json");
            writer.write("""
                    if parsed_body is None:
                        body = await http_response.consume_body_async()
                    else:
                        body = json.dumps(parsed_body).encode('utf-8')
                    """);
        }

        writer.write("""
                if body:
                    codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                    deserializer = codec.create_deserializer(body)
                    body_kwargs = $T.deserialize_kwargs(deserializer)
                    kwargs.update(body_kwargs)
                """, symbol);
    }

    @Override
    protected void generateDocumentBodyShapeDeserializers(
            GenerationContext context,
            Set<Shape> shapes
    ) {
        // No longer needed now that JSONCodec is handling it
    }

    @Override
    protected void deserializePayloadBody(
            GenerationContext context,
            PythonWriter writer,
            Shape operationOrError,
            HttpBinding payloadBinding
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_JSON);
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addImport("smithy_json", "JSONCodec");
        writer.addImport("smithy_core.types", "TimestampFormat");

        var symbolProvider = context.symbolProvider();
        var memberName = symbolProvider.toMemberName(payloadBinding.getMember());
        var target = context.model().expectShape(payloadBinding.getMember().getTarget());

        if (target.hasTrait(StreamingTrait.class)) {
            // If the target is a union, nothing needs to be done here. The stream deserializer will
            // take the response body directly and handle it.
            if (target.isBlobShape()) {
                writer.addImport("smithy_core.aio.types", "AsyncBytesReader");
                writer.write("kwargs[$S] = AsyncBytesReader(http_response.body)", memberName);
            }
            return;
        }

        if (operationOrError.isOperationShape()) {
            writer.write("body = await http_response.consume_body_async()");
        } else {
            // TODO extract error codes in another way
            writer.addStdlibImport("json");
            writer.write("""
                    if parsed_body is None:
                        body = await http_response.consume_body_async()
                    else:
                        body = json.dumps(parsed_body).encode('utf-8')
                    """);
        }

        var deserializerSymbol = symbolProvider.toSymbol(target);

        if (target.isUnionShape()) {
            deserializerSymbol = deserializerSymbol.expectProperty(SymbolProperties.DESERIALIZER);
            writer.write("""
                    if body:
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        deserializer = codec.create_deserializer(body)
                        kwargs[$S] = $T().deserialize(deserializer)
                    """, memberName, deserializerSymbol);
        } else if (target.isStringShape()) {
            writer.write("kwargs[$S] = body.decode('utf-8') if body else \"\"", memberName);
        } else if (target.isBlobShape()) {
            writer.write("kwargs[$S] = body or b\"\"", memberName);
        } else if (target.isDocumentShape()) {
            var schemaSymbol = deserializerSymbol.expectProperty(SymbolProperties.SCHEMA);
            writer.write("""
                    if body:
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        deserializer = codec.create_deserializer(body)
                        kwargs[$S] = deserializer.read_document($T)
                    """, memberName, schemaSymbol);
        } else {
            writer.write("""
                    if body:
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        kwargs[$S] = codec.deserialize(body, $T)
                    """, memberName, deserializerSymbol);
        }
    }

    @Override
    protected void resolveErrorCodeAndMessage(
            GenerationContext context,
            PythonWriter writer,
            Boolean canReadResponseBody
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
        writer.addImport("smithy_http.aio.restjson", "parse_rest_json_error_info");
        writer.writeInline("code, message, parsed_body = await parse_rest_json_error_info(http_response");
        if (!canReadResponseBody) {
            writer.writeInline(", False");
        }
        writer.write(")");
    }

    @Override
    public void wrapInputStream(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_JSON);
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_EVENT_STREAM);
        writer.addImport("smithy_json", "JSONCodec");
        writer.addImport("smithy_core.types", "TimestampFormat");
        writer.addImports("smithy_aws_event_stream.aio", Set.of("AWSEventPublisher", "SigningConfig"));
        writer.addImport("aws_sdk_signers", "AsyncEventSigner");
        writer.write(
                """
                        # TODO - Move this out of the RestJSON generator
                        ctx = request_context.properties
                        event_signer = ctx["auth_scheme"].event_signer(request=request_context.transport_request)
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        publisher = AWSEventPublisher[Any](
                            payload_codec=codec,
                            async_writer=request_context.transport_request.body,  # type: ignore
                            signing_config=SigningConfig(
                                signer=event_signer,
                                signing_properties=ctx["signing_properties"],
                                identity_resolver=ctx["identity_resolver"],
                                identity_properties=ctx["identity_properties"],
                            )
                        )
                        """);
    }

    @Override
    public void wrapOutputStream(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_JSON);
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_EVENT_STREAM);
        writer.addImport("smithy_json", "JSONCodec");
        writer.addImport("smithy_core.aio.types", "AsyncBytesReader");
        writer.addImport("smithy_core.types", "TimestampFormat");
        writer.addImport("smithy_aws_event_stream.aio", "AWSEventReceiver");
        writer.write(
                """
                        codec = JSONCodec(default_timestamp_format=TimestampFormat.EPOCH_SECONDS)
                        receiver = AWSEventReceiver(
                            payload_codec=codec,
                            source=AsyncBytesReader(
                                transport_response.body  # type: ignore
                            ),
                            deserializer=event_deserializer,  # type: ignore
                        )
                        """);
    }
}
