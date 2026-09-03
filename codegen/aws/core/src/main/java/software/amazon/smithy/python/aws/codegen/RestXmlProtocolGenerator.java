/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.RestXmlTrait;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class RestXmlProtocolGenerator implements ProtocolGenerator {
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            // These tests essentially try to assert nan == nan, which is never true.
            // The generator needs protocol-specific assertions before enabling them.
            "RestXmlSupportsNaNFloatHeaderOutputs",
            "RestXmlSupportsNaNFloatOutputs",

            // TODO: support idempotency token autofill
            "QueryIdempotencyTokenAutoFill",

            // TODO: support the endpoint trait
            "RestXmlEndpointTrait",
            "RestXmlEndpointTraitWithHostLabel",
            "RestXmlEndpointTraitWithHostLabelAndHttpBinding",

            // TODO: support the request compression trait
            // https://smithy.io/2.0/spec/behavior-traits.html#smithy-api-requestcompression-trait
            "SDKAppliedContentEncoding_restXml",
            "SDKAppendedGzipAfterProvidedEncoding_restXml");

    @Override
    public ShapeId getProtocol() {
        return RestXmlTrait.ID;
    }

    @Override
    public ApplicationProtocol getApplicationProtocol(GenerationContext context) {
        var service = context.settings().service(context.model());
        var trait = service.expectTrait(RestXmlTrait.class);
        var config = ObjectNode.builder()
                .withMember("http", ArrayNode.fromStrings(trait.getHttp()))
                .withMember("eventStreamHttp", ArrayNode.fromStrings(trait.getEventStreamHttp()))
                .build();
        return ApplicationProtocol.createDefaultHttpApplicationProtocol(config);
    }

    @Override
    public void initializeProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(AwsPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("xml"));
        var serviceSymbol = context.symbolProvider().toSymbol(context.settings().service(context.model()));
        var serviceSchema = serviceSymbol.expectProperty(SymbolProperties.SCHEMA);
        writer.write("$1T($2T)", AwsRuntimeTypes.REST_XML_CLIENT_PROTOCOL, serviceSchema);
    }

    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator()
                .useFileWriter("./tests/test_restxml_protocol.py", "tests.test_restxml_protocol", writer -> {
                    new HttpProtocolTestGenerator(
                            context,
                            getProtocol(),
                            writer,
                            (shape, testCase) -> TESTS_TO_SKIP.contains(testCase.getId())).run();
                });
    }
}
