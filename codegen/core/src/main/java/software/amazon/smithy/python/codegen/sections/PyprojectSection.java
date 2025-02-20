/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import java.util.Map;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * This section controls the entire pyproject.toml
 *
 * <p>An integration may want to append to this if, for instance, it is adding
 * some new dependency that needs to be configured. Note that dependencies
 * themselves should be added when they're introduced in the writers, not here.
 *
 * @param dependencies A mapping of {@link software.amazon.smithy.python.codegen.PythonDependency.Type}
 *                     to a mapping of the package name to {@link SymbolDependency}.
 *                     This contains all the dependencies for the generated client.
 */
@SmithyUnstableApi
public record PyprojectSection(Map<String, Map<String, SymbolDependency>> dependencies) implements CodeSection {}
