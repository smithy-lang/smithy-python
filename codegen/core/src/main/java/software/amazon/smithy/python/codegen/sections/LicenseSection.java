/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * This section controls the entire generated LICENSE
 *
 * <p>An integration may want to use this if they want to programmatically
 * overwrite the generated LICENSE.
 */
@SmithyUnstableApi
public record LicenseSection() implements CodeSection {}
