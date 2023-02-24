/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
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
public record PyprojectSection(Map<String, Map<String, SymbolDependency>> dependencies) implements CodeSection {
}
