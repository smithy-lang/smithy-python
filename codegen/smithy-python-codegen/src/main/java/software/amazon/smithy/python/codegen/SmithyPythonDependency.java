/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import java.util.List;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.python.codegen.PythonDependency.Type;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Dependencies used in the smithy python generator.
 */
@SmithyUnstableApi
public final class SmithyPythonDependency {

    /**
     * The core smithy-python python package.
     *
     * While in development this will use the develop branch.
     */
    public static final PythonDependency SMITHY_PYTHON = new PythonDependency(
            "smithy_python",
            // You'll need to locally install this before we publish
            "==0.0.1",
            Type.DEPENDENCY,
            false
    );

    /**
     * testing framework used in generated functional tests.
     */
    public static final PythonDependency PYTEST = new PythonDependency(
            "pytest",
            ">=7.2.0,<8.0.0",
            Type.TEST_DEPENDENCY,
            false
    );

    /**
     * testing framework used in generated functional tests.
     */
    public static final PythonDependency PYTEST_ASYNCIO = new PythonDependency(
        "pytest-asyncio",
        ">=0.20.3,<0.21.0",
        Type.TEST_DEPENDENCY,
        false
    );

    private SmithyPythonDependency() {}

    /**
     * @return a list of dependencies that are always needed.
     */
    public static List<SymbolDependency> getUnconditionalDependencies() {
        return List.of(SMITHY_PYTHON.getDependency());
    }
}
