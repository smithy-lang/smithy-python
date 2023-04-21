/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;

/**
 * A code section that controls generating the entire auth scheme resolver.
 */
public record GenerateHttpAuthSchemeResolverSection() implements CodeSection {
}
