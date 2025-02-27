/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds a runtime plugin to set generic user agent.
 */
@SmithyInternalApi
public class UserAgentIntegration implements PythonIntegration {
    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (context.applicationProtocol().isHttpProtocol()) {
            return List.of(
                    RuntimeClientPlugin.builder()
                            .pythonPlugin(
                                    SymbolReference.builder()
                                            .symbol(Symbol.builder()
                                                    .namespace(
                                                            SmithyPythonDependency.SMITHY_HTTP.packageName()
                                                                    + ".plugins",
                                                            ".")
                                                    .name("user_agent_plugin")
                                                    .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                                                    .build())
                                            .build())
                            .build());
        } else {
            return List.of();
        }
    }
}
