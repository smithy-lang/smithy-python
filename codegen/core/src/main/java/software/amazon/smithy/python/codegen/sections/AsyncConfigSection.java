/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Section marker emitted after the legacy Config class in config.py.
 *
 * <p>AWS integrations intercept this section to generate the async config
 * subclass (e.g., AsyncBedrockRuntimeConfig) that inherits from AsyncAwsConfig.
 */
@SmithyInternalApi
public record AsyncConfigSection() implements CodeSection {}
