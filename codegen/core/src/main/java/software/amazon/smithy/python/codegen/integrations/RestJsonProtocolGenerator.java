/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.RestJson1Trait;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
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
public class RestJsonProtocolGenerator implements ProtocolGenerator {

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

            // TODO: These tests require a payload even when the httpPayload member is null. Should it?
            "RestJsonHttpWithHeadersButNoPayload",
            "RestJsonHttpWithEmptyStructurePayload",

            // These tests do need to be fixed, but they're being disabled right now
            // since the way protocols work is changing.
            "RestJsonClientPopulatesDefaultValuesInInput",
            "RestJsonClientSkipsTopLevelDefaultValuesInInput",
            "RestJsonClientUsesExplicitlyProvidedMemberValuesOverDefaults",
            "RestJsonClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
            "RestJsonClientPopulatesDefaultsValuesWhenMissingInResponse",
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
    public void initializeProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("json"));
        writer.addImport("smithy_aws_core.aio.protocols", "RestJsonClientProtocol");
        var serviceSymbol = context.symbolProvider().toSymbol(context.settings().service(context.model()));
        var serviceSchema = serviceSymbol.expectProperty(SymbolProperties.SCHEMA);
        writer.write("RestJsonClientProtocol($T)", serviceSchema);
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
}
