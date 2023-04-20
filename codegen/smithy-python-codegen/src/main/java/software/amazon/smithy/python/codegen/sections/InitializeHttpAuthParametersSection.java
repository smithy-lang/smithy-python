/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;

/**
 * A section that controls writing out the auth scheme parameters.
 */
public record InitializeHttpAuthParametersSection() implements CodeSection {
}
