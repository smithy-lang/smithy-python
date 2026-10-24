/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.utils.SmithyInternalApi;

/** Adds modeled request-compression controls to HTTP clients. */
@SmithyInternalApi
public final class RequestCompressionIntegration implements PythonIntegration {
    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (!context.applicationProtocol().isHttpProtocol()) {
            return List.of();
        }
        return List.of(RuntimeClientPlugin.builder()
                // AWS clients inherit the controls and resolvers from AsyncAwsConfig.
                .servicePredicate((model, service) -> !service.hasTrait(ServiceTrait.class))
                .addConfigProperty(ConfigProperty.builder()
                        .name("disable_request_compression")
                        .type(Symbol.builder().name("bool").build())
                        .nullable(false)
                        .documentation("Disable compression on operations that advertise support.")
                        .initialize(w -> w.write("self.disable_request_compression = "
                                + "disable_request_compression if disable_request_compression is not None else False"))
                        .build())
                .addConfigProperty(ConfigProperty.builder()
                        .name("request_min_compression_size_bytes")
                        .type(Symbol.builder().name("int").build())
                        .nullable(false)
                        .documentation("Minimum buffered request size for automatic compression; zero compresses all.")
                        .initialize(w -> w.write("self.request_min_compression_size_bytes = "
                                + "request_min_compression_size_bytes if request_min_compression_size_bytes is not None "
                                + "else 10240"))
                        .build())
                .addConfigProperty(ConfigProperty.builder()
                        .name("request_compression_encoding")
                        .type(Symbol.builder().name("str").build())
                        .documentation("Explicitly request gzip regardless of size; unsupported operations fail.")
                        .build())
                .build());
    }
}
