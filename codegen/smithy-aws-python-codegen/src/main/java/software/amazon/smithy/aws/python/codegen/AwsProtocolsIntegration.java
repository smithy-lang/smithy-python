/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.aws.python.codegen;

import java.util.List;
import software.amazon.smithy.python.codegen.integration.ProtocolGenerator;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds AWS protocols to the generator's list of supported protocols.
 */
@SmithyInternalApi
public class AwsProtocolsIntegration implements PythonIntegration {
    @Override
    public List<ProtocolGenerator> getProtocolGenerators() {
        return List.of();
    }
}
