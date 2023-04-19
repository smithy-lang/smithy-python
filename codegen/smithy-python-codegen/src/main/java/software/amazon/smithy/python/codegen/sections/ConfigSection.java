/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen.sections;

import java.util.List;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.utils.CodeSection;

/**
 * Section that contains the entire generated config object.
 *
 * @param properties The list of properties that need to be present on the config.
 */
public record ConfigSection(List<ConfigProperty> properties) implements CodeSection {
}
