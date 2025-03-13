/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsConfiguration.REGION;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.EndpointParametersSection;
import software.amazon.smithy.python.codegen.sections.EndpointResolverSection;
import software.amazon.smithy.python.codegen.sections.InitDefaultEndpointResolverSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;

public class AwsStandardRegionalEndpointsIntegration implements PythonIntegration {
    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (context.applicationProtocol().isHttpProtocol()) {
            return List.of(
                    RuntimeClientPlugin.builder()
                            .addConfigProperty(REGION)
                            .build());
        } else {
            return List.of();
        }
    }

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        return List.of(
                new RegionalEndpointParametersInterceptor(context),
                new RegionalEndpointResolverInterceptor(context),
                new RegionalInitEndpointResolverInterceptor(context));
    }

    private static final class RegionalEndpointParametersInterceptor
            implements CodeInterceptor<EndpointParametersSection, PythonWriter> {

        private final GenerationContext context;

        public RegionalEndpointParametersInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<EndpointParametersSection> sectionType() {
            return EndpointParametersSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, EndpointParametersSection section) {
            var params = CodegenUtils.getEndpointParametersSymbol(context.settings());

            writer.write("from smithy_aws_core.endpoints.standard_regional import RegionalEndpointParameters");
            writer.write("$L = RegionalEndpointParameters", params.getName());
        }
    }

    private static final class RegionalEndpointResolverInterceptor
            implements CodeInterceptor<EndpointResolverSection, PythonWriter> {

        private final GenerationContext context;

        public RegionalEndpointResolverInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<EndpointResolverSection> sectionType() {
            return EndpointResolverSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, EndpointResolverSection section) {
            var resolver = CodegenUtils.getEndpointResolverSymbol(context.settings());

            writer.write("from smithy_aws_core.endpoints.standard_regional import StandardRegionalEndpointsResolver");
            writer.write("$L = StandardRegionalEndpointsResolver", resolver.getName());
        }
    }

    private static final class RegionalInitEndpointResolverInterceptor
            implements CodeInterceptor<InitDefaultEndpointResolverSection, PythonWriter> {

        private final GenerationContext context;

        public RegionalInitEndpointResolverInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<InitDefaultEndpointResolverSection> sectionType() {
            return InitDefaultEndpointResolverSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, InitDefaultEndpointResolverSection section) {
            var resolver = CodegenUtils.getEndpointResolverSymbol(context.settings());

            String endpointPrefix = context.settings()
                    .service(context.model())
                    .getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getEndpointPrefix)
                    .orElse(context.settings().service().getName());

            writer.write("self.endpoint_resolver = endpoint_resolver or $T(endpoint_prefix=$S)",
                    resolver,
                    endpointPrefix);

        }
    }
}
