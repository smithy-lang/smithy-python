/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import software.amazon.smithy.python.codegen.PythonDependency;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * AWS Dependencies used in the smithy python generator.
 */
@SmithyUnstableApi
public class AwsPythonDependency {

    private AwsPythonDependency() {}

    /**
     * The core aws smithy runtime python package.
     *
     * <p>While in development this will use the develop branch.
     */
    public static final PythonDependency SMITHY_AWS_CORE = new PythonDependency(
            "smithy_aws_core",
            "~=0.2.0",
            PythonDependency.Type.DEPENDENCY,
            false);
}
