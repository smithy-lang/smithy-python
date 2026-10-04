/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.Set;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.protocol.traits.Rpcv2CborTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.generators.ProtocolSettingsField;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * rpcv2Cbor is an RPC protocol: HTTP binding traits are ignored, requests are
 * {@code POST}ed to a fixed URI, and the http config is taken from the protocol trait
 * itself. The runtime behavior lives in the {@code RpcV2CborClientProtocol} Python class
 * in {@code smithy-http}.
 */
@SmithyUnstableApi
public final class Rpcv2CborProtocolGenerator implements ProtocolGenerator {

    // A defaulted member is generated as a plain non-nullable field carrying its default
    // (e.g. `member: int = 0`), so a value left UNSET is indistinguishable from one set
    // to the default by the time serialization runs, and the client always serializes
    // top-level defaults. Every vector that expects those omitted from the body fails,
    // and a clientOptional member cannot be left absent. Tracking explicitness is a
    // shared model-generation change across every protocol; RestJson parks the same set.
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            "RpcV2CborClientPopulatesDefaultValuesInInput",
            "RpcV2CborClientSkipsTopLevelDefaultValuesInInput",
            "RpcV2CborClientUsesExplicitlyProvidedMemberValuesOverDefaults",
            "RpcV2CborClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional");

    @Override
    public ShapeId getProtocol() {
        return Rpcv2CborTrait.ID;
    }

    @Override
    public ApplicationProtocol getApplicationProtocol(GenerationContext context) {
        ServiceShape service = context.settings().service(context.model());
        Rpcv2CborTrait trait = service.expectTrait(Rpcv2CborTrait.class);
        ObjectNode config = ObjectNode.builder()
                .withMember("http", ArrayNode.fromStrings(trait.getHttp()))
                .withMember("eventStreamHttp", ArrayNode.fromStrings(trait.getEventStreamHttp()))
                .build();
        return ApplicationProtocol.createDefaultHttpApplicationProtocol(config);
    }

    @Override
    public void initializeProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("cbor"));
        writer.write("$T(_PROTOCOL_SETTINGS)", RuntimeTypes.RPC_V2_CBOR_CLIENT_PROTOCOL);
    }

    @Override
    public void initializeSyncProtocol(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("cbor"));
        writer.write("$T(_PROTOCOL_SETTINGS)", RuntimeTypes.RPC_V2_CBOR_SYNC_CLIENT_PROTOCOL);
    }

    @Override
    public Set<ProtocolSettingsField> requiredProtocolSettings(GenerationContext context) {
        // The RPC URI is /service/{service_target}/operation/{name}, and the codec
        // resolves document discriminators against the service namespace.
        return Set.of(ProtocolSettingsField.NAMESPACE, ProtocolSettingsField.SERVICE_TARGET);
    }

    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator()
                .useFileWriter("./tests/test_rpcv2cbor_protocol.py", "tests.test_rpcv2cbor_protocol", writer -> {
                    new HttpProtocolTestGenerator(
                            context,
                            getProtocol(),
                            writer,
                            (shape, testCase) -> TESTS_TO_SKIP.contains(testCase.getId())).run();
                });
    }
}
