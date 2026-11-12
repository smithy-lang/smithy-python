/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.traits.EndpointTrait;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds the {@code disable_host_prefix_injection} config field to clients of services with
 * operations that have the {@code smithy.api#endpoint} trait.
 */
@SmithyInternalApi
public final class HostPrefixIntegration implements PythonIntegration {

    private static final ConfigProperty DISABLE_HOST_PREFIX_INJECTION = ConfigProperty.builder()
            .name("disable_host_prefix_injection")
            .type(Symbol.builder().name("bool").build())
            .documentation("Whether to skip prepending operations' modeled host prefixes to the endpoint host.")
            .build();

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return List.of(RuntimeClientPlugin.builder()
                .servicePredicate((model, service) -> TopDownIndex.of(model)
                        .getContainedOperations(service)
                        .stream()
                        .anyMatch(operation -> operation.hasTrait(EndpointTrait.class)))
                .addConfigProperty(DISABLE_HOST_PREFIX_INJECTION)
                .build());
    }
}
