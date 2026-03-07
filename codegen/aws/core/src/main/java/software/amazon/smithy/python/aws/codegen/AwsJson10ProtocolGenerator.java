/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.AwsJson1_0Trait;
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
public final class AwsJson10ProtocolGenerator implements ProtocolGenerator {
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            // TODO: support the request compression trait
            // https://smithy.io/2.0/spec/behavior-traits.html#smithy-api-requestcompression-trait
            "SDKAppliedContentEncoding_awsJson1_0",
            "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_awsJson1_0",

            // TODO: Fix for both REST-JSON and JSON-RPC
            "AwsJson10ClientPopulatesDefaultValuesInInput",
            "AwsJson10ClientSkipsTopLevelDefaultValuesInInput",
            "AwsJson10ClientUsesExplicitlyProvidedMemberValuesOverDefaults",
            "AwsJson10ClientPopulatesDefaultsValuesWhenMissingInResponse",
            "AwsJson10ClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
            "AwsJson10ClientIgnoresDefaultValuesIfMemberValuesArePresentInResponse",

            // TODO: support of the endpoint trait
            "AwsJson10EndpointTraitWithHostLabel",
            "AwsJson10EndpointTrait",

            // TODO: support client error-correction behavior when the server
            // omits required values in modeled error responses.
            "AwsJson10ClientErrorCorrectsWhenServerFailsToSerializeRequiredValues",
            "AwsJson10ClientErrorCorrectsWithDefaultValuesWhenServerFailsToSerializeRequiredValues");

    @Override
    public ShapeId getProtocol() {
        return AwsJson1_0Trait.ID;
    }

    @Override
    public ApplicationProtocol getApplicationProtocol(GenerationContext context) {
        var service = context.settings().service(context.model());
        var trait = service.expectTrait(AwsJson1_0Trait.class);
        var config = ObjectNode.builder()
                .withMember("http", ArrayNode.fromStrings(trait.getHttp()))
                .withMember("eventStreamHttp", ArrayNode.fromStrings(trait.getEventStreamHttp()))
                .build();
        return ApplicationProtocol.createDefaultHttpApplicationProtocol(config);
    }

    @Override
    public void initializeProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(AwsPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("json"));
        writer.addImport("smithy_aws_core.aio.protocols", "AwsJson10ClientProtocol");
        var serviceSymbol = context.symbolProvider().toSymbol(context.settings().service(context.model()));
        var serviceSchema = serviceSymbol.expectProperty(SymbolProperties.SCHEMA);
        writer.write("AwsJson10ClientProtocol($T)", serviceSchema);
    }

    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator()
                .useFileWriter("./tests/test_awsjson10_protocol.py", "tests.test_awsjson10_protocol", writer -> {
                    new HttpProtocolTestGenerator(
                            context,
                            getProtocol(),
                            writer,
                            (shape, testCase) -> TESTS_TO_SKIP.contains(testCase.getId())).run();
                });
    }
}
