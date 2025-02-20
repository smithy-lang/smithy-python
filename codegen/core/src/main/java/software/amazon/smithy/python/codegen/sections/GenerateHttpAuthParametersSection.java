/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import java.util.Map;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A section that controls generating the HttpAuthParameters class.
 *
 * @param properties A map of property names to types for properties that must
 *                   be present on the parameters object.
 */
@SmithyInternalApi
public record GenerateHttpAuthParametersSection(Map<String, Symbol> properties) implements CodeSection {}
