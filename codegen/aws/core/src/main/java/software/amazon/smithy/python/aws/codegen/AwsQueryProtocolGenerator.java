/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.AwsQueryTrait;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class AwsQueryProtocolGenerator implements ProtocolGenerator {
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            // TODO: support the request compression trait
            // https://smithy.io/2.0/spec/behavior-traits.html#smithy-api-requestcompression-trait
            "SDKAppliedContentEncoding_awsQuery",
            "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_awsQuery",

            // TODO: support idempotency token autofill
            "QueryProtocolIdempotencyTokenAutoFill",

            // This test asserts nan == nan, which is never true.
            // We should update the generator to make specific assertions for these.
            "AwsQuerySupportsNaNFloatOutputs",

            // TODO: support of the endpoint trait
            "AwsQueryEndpointTraitWithHostLabel",
            "AwsQueryEndpointTrait");

    @Override
    public ShapeId getProtocol() {
        return AwsQueryTrait.ID;
    }

    @Override
    public ApplicationProtocol getApplicationProtocol(GenerationContext context) {
        return ApplicationProtocol.createDefaultHttpApplicationProtocol();
    }

    @Override
    public void initializeProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(AwsPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("xml"));
        var service = context.settings().service(context.model());
        var serviceSymbol = context.symbolProvider().toSymbol(service);
        var serviceSchema = serviceSymbol.expectProperty(SymbolProperties.SCHEMA);
        var version = service.getVersion();
        writer.write("$1T($2T, $3S)", AwsRuntimeTypes.AWS_QUERY_CLIENT_PROTOCOL, serviceSchema, version);
    }

    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator()
                .useFileWriter("./tests/test_awsquery_protocol.py", "tests.test_awsquery_protocol", writer -> {
                    new HttpProtocolTestGenerator(
                            context,
                            getProtocol(),
                            writer,
                            (shape, testCase) -> TESTS_TO_SKIP.contains(testCase.getId())).run();
                });
    }
}
