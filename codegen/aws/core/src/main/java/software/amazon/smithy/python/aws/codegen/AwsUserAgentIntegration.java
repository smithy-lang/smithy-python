/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Collections;
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds a runtime plugin to set user agent.
 */
@SmithyInternalApi
public class AwsUserAgentIntegration implements PythonIntegration {
    @Override
    public List<RuntimeClientPlugin> getClientPlugins() {
        return List.of(
                RuntimeClientPlugin.builder()
                        .addConfigProperty(ConfigProperty.builder()
                                // TODO: This is the name used in boto, but potentially could be user_agent_prefix.  Depends on backwards compat strategy.
                                .name("user_agent_extra")
                                .documentation("Additional suffix to be added to the user agent")
                                .type(Symbol.builder().name("str").build()) // TODO: Should common types like this be defined as constants somewhere?
                                .nullable(true)
                                .build())
                        .pythonPlugin(
                                SymbolReference.builder()
                                        .symbol(Symbol.builder()
                                                .namespace(AwsPythonDependency.SMITHY_AWS_CORE.packageName() + ".plugins", ".")
                                                .name("user_agent_plugin")
                                                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                                                .build())
                                        .build()
                        )
                        .build()
        );
    }

}
