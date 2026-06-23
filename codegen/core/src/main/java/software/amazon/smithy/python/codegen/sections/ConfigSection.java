/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import java.util.List;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Section that contains the entire generated config object.
 *
 * @param properties The list of properties that need to be present on the config.
 */
@SmithyInternalApi
public record ConfigSection(List<ConfigProperty> properties) implements CodeSection {

    /** Section for a single config property's class-level field declaration. */
    public record PropertyDeclarationSection(ConfigProperty property) implements CodeSection {}

    /** Section before property declarations, for injecting class-level fields. */
    public record PrePropertyDeclarationsSection(List<ConfigProperty> properties) implements CodeSection {}

    /** Section before property initializations in __init__, for injecting setup code. */
    public record PreInitializePropertiesSection(List<ConfigProperty> properties) implements CodeSection {}
}
