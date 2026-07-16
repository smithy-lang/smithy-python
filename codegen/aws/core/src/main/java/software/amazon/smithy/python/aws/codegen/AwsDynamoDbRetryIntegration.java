/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;

/**
 * Registers DynamoDB's retry defaults as a service-scoped client plugin on
 * DynamoDB / DynamoDB Streams clients.
 */
public final class AwsDynamoDbRetryIntegration implements PythonIntegration {

    private static final Set<String> DYNAMODB_SDK_IDS = Set.of("DynamoDB", "DynamoDB Streams");

    private static final SymbolReference DYNAMODB_RETRY_PLUGIN = SymbolReference.builder()
            .symbol(Symbol.builder()
                    .namespace("smithy_aws_core.plugins", ".")
                    .name("dynamodb_retry_plugin")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .build();

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.getTrait(ServiceTrait.class)
                                .map(trait -> DYNAMODB_SDK_IDS.contains(trait.getSdkId()))
                                .orElse(false))
                        .pythonPlugin(DYNAMODB_RETRY_PLUGIN)
                        .build());
    }
}
