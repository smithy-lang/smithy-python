/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;

public class SetupGeneratorTest {

    /**
     * When a client depends on smithy_http (the common case, since all transports default to aiohttp),
     * an {@code awscrt} extra is exposed that re-exports smithy_http's own awscrt extra so the version
     * constraint stays sourced from smithy-http.
     */
    @Test
    public void exposesAwscrtExtraForSmithyHttpDependency() {
        var smithyHttp = SmithyPythonDependency.SMITHY_HTTP.getDependency();
        Map<String, SymbolDependency> dependencies = Map.of(smithyHttp.getPackageName(), smithyHttp);

        var extras = SetupGenerator.collectOptionalDependencies(dependencies);

        assertEquals(
                Map.of("awscrt", List.of("smithy_http[awscrt]" + smithyHttp.getVersion())),
                extras);
    }
}
