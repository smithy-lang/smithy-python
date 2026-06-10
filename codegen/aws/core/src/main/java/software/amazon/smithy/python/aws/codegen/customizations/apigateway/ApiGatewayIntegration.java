/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen.customizations.apigateway;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds a runtime plugin that sets the {@code Accept: application/json} header on
 * Amazon API Gateway requests.
 */
@SmithyInternalApi
public class ApiGatewayIntegration implements PythonIntegration {

    private static final ShapeId API_GATEWAY_SERVICE_ID =
            ShapeId.from("com.amazonaws.apigateway#BackplaneControlService");

    public static final String ACCEPT_HEADER_PLUGIN = """
            def accept_header_plugin(config: $1T):
                config.interceptors.append($2T())
            """;

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (!context.applicationProtocol().isHttpProtocol()) {
            return List.of();
        }

        final String pluginFile = "accept_header";
        final String moduleName = context.settings().moduleName();

        final SymbolReference acceptHeaderPlugin = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .namespace(String.format("%s.%s", moduleName, pluginFile), ".")
                        .definitionFile(String.format("./src/%s/%s.py", moduleName, pluginFile))
                        .name("accept_header_plugin")
                        .build())
                .build();
        final SymbolReference acceptHeaderInterceptor = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .namespace("smithy_aws_core.interceptors.api_gateway", ".")
                        .name("ApiGatewayAcceptHeaderInterceptor")
                        .build())
                .build();

        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.getId().equals(API_GATEWAY_SERVICE_ID))
                        .pythonPlugin(acceptHeaderPlugin)
                        .writeAdditionalFiles((c) -> {
                            String filename = "src/%s/%s.py".formatted(moduleName, pluginFile);
                            c.writerDelegator()
                                    .useFileWriter(
                                            filename,
                                            moduleName + ".",
                                            writer -> writer.write(ACCEPT_HEADER_PLUGIN,
                                                    CodegenUtils.getConfigSymbol(c.settings()),
                                                    acceptHeaderInterceptor));
                            return List.of(filename);
                        })
                        .build());
    }
}
