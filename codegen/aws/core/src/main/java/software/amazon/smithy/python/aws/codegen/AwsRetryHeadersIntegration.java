/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SyncVariant;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds the interceptor that sends the retry information headers to clients of AWS
 * services.
 */
@SmithyInternalApi
public final class AwsRetryHeadersIntegration implements PythonIntegration {

    private static final String PLUGIN_FILE = "retry_headers";

    private static final String RETRY_HEADERS_PLUGIN = """
            def aws_retry_headers_plugin(config: $1T) -> None:
                config.interceptors.append($2T())
            """;

    // The interceptor has no async twin, so the sync plugin gets the same symbol.
    private static final Symbol INTERCEPTOR = Symbol.builder()
            .namespace("smithy_aws_core.interceptors.retry_headers", ".")
            .name("RetryHeadersInterceptor")
            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
            .build();

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (!CodegenUtils.isAwsService(context)) {
            return List.of();
        }

        final SymbolReference plugin = SymbolReference.builder()
                .symbol(CodegenUtils.aioSymbol(context.settings(), PLUGIN_FILE, "aws_retry_headers_plugin"))
                .build();

        return List.of(
                RuntimeClientPlugin.builder()
                        .pythonPlugin(plugin)
                        .writeAdditionalFiles((c) -> {
                            var filename = plugin.getSymbol().getDefinitionFile();
                            var asyncConfig = CodegenUtils.getAsyncConfigSymbol(c.settings(), c.model());
                            c.writerDelegator()
                                    .useFileWriter(filename,
                                            plugin.getSymbol().getNamespace(),
                                            writer -> writer.write(RETRY_HEADERS_PLUGIN,
                                                    asyncConfig,
                                                    INTERCEPTOR));
                            var syncFile = SyncVariant.writeSyncTwin(c,
                                    plugin.getSymbol(),
                                    RETRY_HEADERS_PLUGIN,
                                    asyncConfig,
                                    INTERCEPTOR);
                            return List.of(filename, syncFile);
                        })
                        .build());
    }
}
