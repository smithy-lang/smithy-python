/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsConfiguration.REGION;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
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
                new RegionalInitEndpointResolverInterceptor(context));
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
            String endpointPrefix = context.settings()
                    .service(context.model())
                    .getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getEndpointPrefix)
                    .orElse(context.settings().service().getName());

            writer.addImport("smithy_aws_core.endpoints.standard_regional",
                    "StandardRegionalEndpointsResolver",
                    "_RegionalResolver");
            writer.write(
                    "self.endpoint_resolver = endpoint_resolver or _RegionalResolver(endpoint_prefix=$S)",
                    endpointPrefix);

        }
    }
}
