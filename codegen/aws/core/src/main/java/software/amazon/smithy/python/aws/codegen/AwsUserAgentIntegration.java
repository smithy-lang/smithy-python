/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds a runtime plugin to set user agent.
 */
@SmithyInternalApi
public class AwsUserAgentIntegration implements PythonIntegration {

    public static final String USER_AGENT_PLUGIN = """
            def aws_user_agent_plugin(config: $1T):
                config.interceptors.append(
                    $2T(
                        ua_suffix=config.user_agent_extra,
                        ua_app_id=config.sdk_ua_app_id,
                        sdk_version=$3T,
                        service_id=$4S,
                    )
                )
            """;

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (context.applicationProtocol().isHttpProtocol()) {
            final ConfigProperty userAgentExtra = ConfigProperty.builder()
                    .name("user_agent_extra")
                    .documentation("Additional suffix to be added to the User-Agent header.")
                    .type(Symbol.builder().name("str").build())
                    .nullable(true)
                    .build();

            final ConfigProperty uaAppId = ConfigProperty.builder()
                    .name("sdk_ua_app_id")
                    .documentation(
                            "A unique and opaque application ID that is appended to the User-Agent header.")
                    .type(Symbol.builder().name("str").build())
                    .nullable(true)
                    .build();

            final String user_agent_plugin_file = "user_agent";

            final String moduleName = context.settings().moduleName();
            final SymbolReference userAgentPlugin = SymbolReference.builder()
                    .symbol(Symbol.builder()
                            .namespace(String.format("%s.%s",
                                    moduleName,
                                    user_agent_plugin_file.replace('/', '.')), ".")
                            .definitionFile(String
                                    .format("./%s/%s.py", moduleName, user_agent_plugin_file))
                            .name("aws_user_agent_plugin")
                            .build())
                    .build();
            final SymbolReference userAgentInterceptor = SymbolReference.builder()
                    .symbol(Symbol.builder()
                            .namespace("smithy_aws_core.interceptors.user_agent", ".")
                            .name("UserAgentInterceptor")
                            .build())
                    .build();
            final SymbolReference versionSymbol = SymbolReference.builder()
                    .symbol(Symbol.builder()
                            .namespace(moduleName, ".")
                            .name("__version__")
                            .build())
                    .build();

            final String serviceId = context.settings()
                    .service(context.model())
                    .getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElse(context.settings().service().getName())
                    .replace(' ', '_');

            return List.of(
                    RuntimeClientPlugin.builder()
                            .addConfigProperty(userAgentExtra)
                            .addConfigProperty(uaAppId)
                            .pythonPlugin(userAgentPlugin)
                            .writeAdditionalFiles((c) -> {
                                String filename = "%s/%s.py".formatted(moduleName, user_agent_plugin_file);
                                c.writerDelegator()
                                        .useFileWriter(
                                                filename,
                                                moduleName + ".",
                                                writer -> {
                                                    writer.write(USER_AGENT_PLUGIN,
                                                            CodegenUtils.getConfigSymbol(c.settings()),
                                                            userAgentInterceptor,
                                                            versionSymbol,
                                                            serviceId);

                                                });
                                return List.of(filename);
                            })
                            .build());
        } else {
            return List.of();
        }
    }

}
