/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.AwsJson1_0Trait;
import software.amazon.smithy.aws.traits.protocols.AwsJson1_1Trait;
import software.amazon.smithy.aws.traits.protocols.RestJson1Trait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds configurable JSON deserialization to clients that support a JSON protocol.
 */
@SmithyInternalApi
public final class JsonDeserializationIntegration implements PythonIntegration {
    private static final Set<ShapeId> JSON_PROTOCOLS = Set.of(
            RestJson1Trait.ID,
            AwsJson1_0Trait.ID,
            AwsJson1_1Trait.ID);

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var mode = Symbol.builder()
                .name("JSONDeserializationMode")
                .namespace("smithy_json", ".")
                .addDependency(SmithyPythonDependency.SMITHY_JSON)
                .build();
        var plugin = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .name("json_deserialization_plugin")
                        .namespace("smithy_json.plugins", ".")
                        .addDependency(SmithyPythonDependency.SMITHY_JSON)
                        .build())
                .build();
        var property = ConfigProperty.builder()
                .name("json_deserialization_mode")
                .type(mode)
                .documentation(
                        "Controls whether JSON response payloads are deserialized eagerly or incrementally.")
                .nullable(true)
                .build();

        return List.of(RuntimeClientPlugin.builder()
                .servicePredicate(JsonDeserializationIntegration::usesJsonProtocol)
                .addConfigProperty(property)
                .pythonPlugin(plugin)
                .build());
    }

    static boolean usesJsonProtocol(Model model, ServiceShape service) {
        return ServiceIndex.of(model)
                .getProtocols(service)
                .keySet()
                .stream()
                .anyMatch(JSON_PROTOCOLS::contains);
    }
}
