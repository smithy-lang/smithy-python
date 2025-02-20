/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Integration that registers {@link RestJsonProtocolGenerator}.
 */
@SmithyInternalApi
public final class RestJsonIntegration implements PythonIntegration {
    @Override
    public List<ProtocolGenerator> getProtocolGenerators() {
        return List.of(new RestJsonProtocolGenerator());
    }
}
