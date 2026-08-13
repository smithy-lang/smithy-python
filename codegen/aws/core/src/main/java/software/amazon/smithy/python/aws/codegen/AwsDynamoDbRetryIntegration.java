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
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;

/**
 * Generates DynamoDB's retry defaults as a service-scoped client plugin on
 * DynamoDB / DynamoDB Streams clients.
 */
public final class AwsDynamoDbRetryIntegration implements PythonIntegration {

    private static final Set<String> DYNAMODB_SDK_IDS = Set.of("DynamoDB", "DynamoDB Streams");

    public static final String DYNAMODB_RETRY_MODULE = """
            _DYNAMODB_DEFAULT_MAX_ATTEMPTS = 4
            _DYNAMODB_DEFAULT_BACKOFF_SCALE = 0.025
            _DYNAMODB_DEFAULT_MAX_BACKOFF = 20


            class _RetryConfig(Protocol):
                retry_strategy: $1T | $2T | None


            def dynamodb_retry_plugin(config: _RetryConfig) -> None:
                \"\"\"Apply DynamoDB's standard-mode retry defaults for any option left unset.\"\"\"
                retry_strategy = config.retry_strategy
                if retry_strategy is not None and not isinstance(
                    retry_strategy, $2T
                ):
                    return

                if isinstance(retry_strategy, $2T):
                    # Explicit options take precedence over separately resolved fields.
                    retry_mode = retry_strategy.retry_mode
                    max_attempts = retry_strategy.max_attempts
                else:
                    # Read independently resolved AsyncConfig fields when available. A legacy
                    # Config has no scalar retry fields, so None represents an unset value.
                    retry_mode = getattr(config, "retry_mode", None) or "standard"
                    max_attempts = getattr(config, "max_attempts", None)
                    source_of = getattr(config, "source_of", None)
                    if (
                        source_of is not None
                        and source_of("max_attempts") == $4T.DEFAULT
                    ):
                        max_attempts = None

                if retry_mode != "standard":
                    return

                config.retry_strategy = $3T(
                    max_attempts=(
                        max_attempts
                        if max_attempts is not None
                        else _DYNAMODB_DEFAULT_MAX_ATTEMPTS
                    ),
                    backoff_strategy=$5T(
                        backoff_scale_value=_DYNAMODB_DEFAULT_BACKOFF_SCALE,
                        max_backoff=_DYNAMODB_DEFAULT_MAX_BACKOFF,
                        jitter_type=$6T.FULL,
                    ),
                )
            """;

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        final String pluginFile = "retries";
        final String moduleName = context.settings().moduleName();

        final SymbolReference dynamodbRetryPlugin = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .namespace(String.format("%s.%s", moduleName, pluginFile), ".")
                        .definitionFile(String.format("./src/%s/%s.py", moduleName, pluginFile))
                        .name("dynamodb_retry_plugin")
                        .build())
                .build();
        final Symbol retryStrategy = Symbol.builder()
                .namespace("smithy_core.aio.interfaces.retries", ".")
                .name("RetryStrategy")
                .build();
        final Symbol retryStrategyOptions = Symbol.builder()
                .namespace("smithy_core.retries", ".")
                .name("RetryStrategyOptions")
                .build();
        final Symbol standardRetryStrategy = Symbol.builder()
                .namespace("smithy_core.aio.retries", ".")
                .name("StandardRetryStrategy")
                .build();
        final Symbol configSource = Symbol.builder()
                .namespace("smithy_aws_core.config", ".")
                .name("ConfigSource")
                .build();
        final Symbol exponentialBackoffStrategy = Symbol.builder()
                .namespace("smithy_core.retries", ".")
                .name("ExponentialRetryBackoffStrategy")
                .build();
        final Symbol exponentialBackoffJitterType = Symbol.builder()
                .namespace("smithy_core.retries", ".")
                .name("ExponentialBackoffJitterType")
                .build();

        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.getTrait(ServiceTrait.class)
                                .map(trait -> DYNAMODB_SDK_IDS.contains(trait.getSdkId()))
                                .orElse(false))
                        .pythonPlugin(dynamodbRetryPlugin)
                        .writeAdditionalFiles((c) -> {
                            String filename = "src/%s/%s.py".formatted(moduleName, pluginFile);
                            c.writerDelegator()
                                    .useFileWriter(
                                            filename,
                                            moduleName + ".",
                                            writer -> {
                                                writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
                                                writer.addDependency(AwsPythonDependency.SMITHY_AWS_CORE);
                                                writer.addStdlibImport("typing", "Protocol");
                                                writer.write(
                                                        DYNAMODB_RETRY_MODULE,
                                                        retryStrategy,
                                                        retryStrategyOptions,
                                                        standardRetryStrategy,
                                                        configSource,
                                                        exponentialBackoffStrategy,
                                                        exponentialBackoffJitterType);
                                            });
                            return List.of(filename);
                        })
                        .build());
    }
}
