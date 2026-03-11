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
            .type(Symbol.builder().name("str | None").build())
            .documentation(" The AWS region to connect to. The configured region is used to "
                    + "determine the service endpoint.")
            .nullable(false)
            .useDescriptor(true)
            .validator(Symbol.builder()
                    .name("validate_region")
                    .namespace("smithy_aws_core.config.validators", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .build();

    public static final ConfigProperty RETRY_STRATEGY = ConfigProperty.builder()
            .name("retry_strategy")
            .type(Symbol.builder()
                    .name("RetryStrategy | RetryStrategyOptions | None")
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
            .nullable(false)
            .useDescriptor(true)
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

    public static final ConfigProperty USER_AGENT_EXTRA = ConfigProperty.builder()
            .name("user_agent_extra")
            .type(Symbol.builder().name("str").build())
            .documentation("Additional suffix to be appended to the User-Agent header.")
            .nullable(false)
            .useDescriptor(true)
            .defaultValue("''")
            .build();

    public static final ConfigProperty SDK_UA_APP_ID = ConfigProperty.builder()
            .name("sdk_ua_app_id")
            .type(Symbol.builder().name("str").build())
            .documentation("A unique and opaque application ID that is appended to the User-Agent header.")
            .nullable(false)
            .useDescriptor(true)
            .defaultValue("''")
            .build();

    public static final ConfigProperty ENDPOINT_URL = ConfigProperty.builder()
            .name("endpoint_url")
            .type(Symbol.builder().name("str").build())
            .documentation("The endpoint URL to use for requests. If not set, the standard endpoint for the service and region will be used.")
            .nullable(true)
            .useDescriptor(true)
            .build();
}
