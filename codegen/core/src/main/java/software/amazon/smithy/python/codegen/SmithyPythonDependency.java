/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
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
     * <p>While in development this will use the develop branch.
     */
    public static final PythonDependency SMITHY_CORE = new PythonDependency(
            "smithy_core",
            "~=0.2.0",
            Type.DEPENDENCY,
            false);

    /**
     * The core smithy-python python package.
     *
     * <p>While in development this will use the develop branch.
     */
    public static final PythonDependency SMITHY_HTTP = new PythonDependency(
            "smithy_http",
            "~=0.3.0",
            Type.DEPENDENCY,
            false);

    /**
     * The awscrt package.
     */
    public static final PythonDependency AWS_CRT = new PythonDependency(
            "awscrt",
            "~=0.28.2",
            Type.DEPENDENCY,
            false);

    /**
     * The aiohttp package.
     */
    public static final PythonDependency AIO_HTTP = new PythonDependency(
            "aiohttp",
            "~=3",
            Type.DEPENDENCY,
            false);

    /**
     * The core smithy-json python package.
     */
    public static final PythonDependency SMITHY_JSON = new PythonDependency(
            "smithy_json",
            "~=0.2.0",
            Type.DEPENDENCY,
            false);

    /**
     * EventStream implementations for application/vnd.amazon.eventstream.
     */
    public static final PythonDependency SMITHY_AWS_EVENT_STREAM = new PythonDependency(
            "smithy_aws_event_stream",
            "~=0.2.0",
            Type.DEPENDENCY,
            false);

    /**
     * Smithy core functionality for AWS.
     */
    public static final PythonDependency SMITHY_AWS_CORE = new PythonDependency(
            "smithy_aws_core",
            "~=0.2.0",
            Type.DEPENDENCY,
            false);

    /**
     * testing framework used in generated functional tests.
     */
    public static final PythonDependency PYTEST = new PythonDependency(
            "pytest",
            ">=7.2.0,<8.0.0",
            Type.TEST_DEPENDENCY,
            false);

    /**
     * testing framework used in generated functional tests.
     */
    public static final PythonDependency PYTEST_ASYNCIO = new PythonDependency(
            "pytest-asyncio",
            ">=0.20.3,<0.21.0",
            Type.TEST_DEPENDENCY,
            false);

    /**
     * library used for documentation generation
     */
    public static final PythonDependency SPHINX = new PythonDependency(
            "sphinx",
            ">=8.2.3",
            Type.DOCS_DEPENDENCY,
            false);

    /**
     * sphinx theme
     */
    public static final PythonDependency SPHINX_PYDATA_THEME = new PythonDependency(
            "pydata-sphinx-theme",
            ">=0.16.1",
            Type.DOCS_DEPENDENCY,
            false);

    private SmithyPythonDependency() {}

    /**
     * @return a list of dependencies that are always needed.
     */
    public static List<SymbolDependency> getUnconditionalDependencies() {
        return List.of(SMITHY_CORE.getDependency());
    }
}
