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
    private AwsConfiguration() {
    }

    public static final ConfigProperty REGION = ConfigProperty.builder()
            .name("region")
            .type(Symbol.builder().name("str").build())
            .documentation(" The AWS region to connect to. The configured region is used to "
                    + "determine the service endpoint.")
            .build();
}
