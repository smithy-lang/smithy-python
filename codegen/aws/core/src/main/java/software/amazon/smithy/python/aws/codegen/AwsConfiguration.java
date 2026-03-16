/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Common configuration for AWS Clients.
 */
@SmithyUnstableApi
public final class AwsConfiguration {
    private AwsConfiguration() {}

    public static final ConfigProperty REGION = ConfigProperty.builder()
            .name("region")
            .type(Symbol.builder().name("str").build())
            .documentation("The AWS region to connect to. The configured region is used to "
                    + "determine the service endpoint.")
            .build();

    public static final ConfigProperty RETRY_STRATEGY = ConfigProperty.builder()
            .name("retry_strategy")
            .type(Symbol.builder()
                    .name("RetryStrategy | RetryStrategyOptions")
                    .addReference(Symbol.builder()
                            .name("RetryStrategy")
                            .namespace("smithy_core.interfaces.retries", ".")
                            .addDependency(software.amazon.smithy.python.codegen.SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .addReference(Symbol.builder()
                            .name("RetryStrategyOptions")
                            .namespace("smithy_core.retries", ".")
                            .addDependency(software.amazon.smithy.python.codegen.SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build())
            .documentation(
                    "The retry strategy or options for configuring retry behavior. Can be either a configured RetryStrategy or RetryStrategyOptions to create one.")
            .build();

    /**
     * AWS-specific metadata for descriptor-based config properties.
     */
    public static final AwsConfigPropertyMetadata REGION_METADATA = AwsConfigPropertyMetadata.builder()
            .validator(Symbol.builder()
                    .name("validate_region")
                    .namespace("smithy_aws_core.config.validators", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .build();
    /**
     * AWS-specific metadata for descriptor-based config properties.
     */
    public static final AwsConfigPropertyMetadata RETRY_STRATEGY_METADATA = AwsConfigPropertyMetadata.builder()
            .validator(Symbol.builder()
                    .name("validate_retry_strategy")
                    .namespace("smithy_aws_core.config.validators", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .customResolver(Symbol.builder()
                    .name("resolve_retry_strategy")
                    .namespace("smithy_aws_core.config.custom_resolvers", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .defaultValue("RetryStrategyOptions(retry_mode=\"standard\")")
            .build();
}
