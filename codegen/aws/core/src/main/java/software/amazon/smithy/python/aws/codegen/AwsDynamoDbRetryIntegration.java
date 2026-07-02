/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.InitRetryStrategyResolverSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;

/**
 * Injects DynamoDB's default retry options (max attempts 4, 25ms non-throttling
 * base backoff).
 */
public final class AwsDynamoDbRetryIntegration implements PythonIntegration {

    private static final Set<String> DYNAMODB_SDK_IDS = Set.of("DynamoDB", "DynamoDB Streams");

    private static final double DYNAMODB_BASE_BACKOFF_SECONDS = 0.025;
    private static final int DYNAMODB_MAX_ATTEMPTS = 4;

    private static boolean isDynamoDb(GenerationContext context) {
        return context.settings()
                .service(context.model())
                .getTrait(ServiceTrait.class)
                .map(trait -> DYNAMODB_SDK_IDS.contains(trait.getSdkId()))
                .orElse(false);
    }

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        if (!isDynamoDb(context)) {
            return List.of();
        }
        return List.of(new DynamoDbRetryStrategyResolverInterceptor());
    }

    private static final class DynamoDbRetryStrategyResolverInterceptor
            implements CodeInterceptor<InitRetryStrategyResolverSection, PythonWriter> {

        @Override
        public Class<InitRetryStrategyResolverSection> sectionType() {
            return InitRetryStrategyResolverSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, InitRetryStrategyResolverSection section) {
            writer.write(
                    "self._retry_strategy_resolver = $T(default_max_attempts=$L, default_backoff_scale=$L)",
                    RuntimeTypes.RETRY_STRATEGY_RESOLVER,
                    DYNAMODB_MAX_ATTEMPTS,
                    DYNAMODB_BASE_BACKOFF_SECONDS);
        }
    }
}
