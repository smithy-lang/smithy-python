/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

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
                        .addConfigProperty(
                                ConfigProperty.builder()
                                        .name("user_agent_extra")
                                        .documentation("Additional suffix to be added to the User-Agent header.")
                                        .type(Symbol.builder().name("str").build())
                                        .nullable(true)
                                        .build())
                        .addConfigProperty(
                                ConfigProperty.builder()
                                        .name("sdk_ua_app_id")
                                        .documentation(
                                                "A unique and opaque application ID that is appended to the User-Agent header.")
                                        .type(Symbol.builder().name("str").build())
                                        .nullable(true)
                                        .build())
                        .pythonPlugin(
                                SymbolReference.builder()
                                        .symbol(Symbol.builder()
                                                .namespace(
                                                        AwsPythonDependency.SMITHY_AWS_CORE.packageName() + ".plugins",
                                                        ".")
                                                .name("user_agent_plugin")
                                                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                                                .build())
                                        .build())
                        .build());
    }

}
