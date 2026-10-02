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
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.generators.ProtocolSettingsField;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class RestXmlProtocolGenerator implements ProtocolGenerator {
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            // TODO: support the request compression trait
            // https://smithy.io/2.0/spec/behavior-traits.html#smithy-api-requestcompression-trait
            "SDKAppliedContentEncoding_restXml",
            "SDKAppendedGzipAfterProvidedEncoding_restXml",

            // TODO: support idempotency token autofill
            "QueryIdempotencyTokenAutoFill",

            // TODO: support of the endpoint trait
            "RestXmlEndpointTraitWithHostLabelAndHttpBinding",
            "RestXmlEndpointTraitWithHostLabel",
            "RestXmlEndpointTrait");

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
        writer.write("$T(_PROTOCOL_SETTINGS)", AwsRuntimeTypes.REST_XML_CLIENT_PROTOCOL);
    }

    @Override
    public Set<ProtocolSettingsField> requiredProtocolSettings(GenerationContext context) {
        // The service's @xmlNamespace is the default namespace of request payloads.
        return Set.of(ProtocolSettingsField.XML_NAMESPACE);
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
