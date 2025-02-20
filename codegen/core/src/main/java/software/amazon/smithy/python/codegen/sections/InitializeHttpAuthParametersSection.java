/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A section that controls writing out the auth scheme parameters.
 */
@SmithyInternalApi
public record InitializeHttpAuthParametersSection() implements CodeSection {}
