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

    // These two require distinguishing a member left UNSET from one explicitly set to
    // its default value. The generated dataclass models a defaulted member as a plain
    // non-nullable field carrying the default (e.g. `member: int = 0`), so the two are
    // indistinguishable by the time serialization runs: the top-level strip cannot tell
    // an explicit "hi" from an omitted one, and a clientOptional member cannot be left
    // absent. Tracking explicitness is a shared model-generation change across every
    // protocol; RestJson parks the same cases. The other two default tests
    // (PopulatesDefaultValuesInInput, SkipsTopLevelDefaultValuesInInput) do pass.
    private static final Set<String> TESTS_TO_SKIP = Set.of(
            "RpcV2CborClientUsesExplicitlyProvidedValuesInTopLevel",
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
        writer.addDependency(SmithyPythonDependency.SMITHY_CBOR);
        writer.write("$T(_PROTOCOL_SETTINGS)", RuntimeTypes.RPC_V2_CBOR_CLIENT_PROTOCOL);
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
