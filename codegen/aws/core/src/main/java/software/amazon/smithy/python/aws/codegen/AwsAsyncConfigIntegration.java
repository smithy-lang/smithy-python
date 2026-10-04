/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import java.util.Optional;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.generators.ConfigBackend;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Contributes the AWS resolution backend: the generated config classes inherit the
 * AWS config bases ({@code AwsConfigBase}/{@code AwsConfig}/{@code AsyncAwsConfig}),
 * their {@code resolve()} accepts the shared-config-file parameters, and their
 * {@code _FIELDS} carry the AWS region/endpoint/credential resolvers.
 *
 * <p>Class emission stays in the core config generator; this only supplies what is
 * AWS-specific, so AWS-ness never decides the sync/async shape.
 */
@SmithyInternalApi
public class AwsAsyncConfigIntegration implements PythonIntegration {

    // Fields already carried by AwsConfigBase._FIELDS (spread by writeExtraFields). The
    // core generator skips emitting a _FIELDS entry and overrides key for these.
    private static final Set<String> PREDEFINED_CONFIG_FIELDS = Set.of(
            "region",
            "retry_mode",
            "max_attempts",
            "endpoint_uri",
            "aws_access_key_id",
            "aws_secret_access_key",
            "aws_session_token",
            "aws_credentials_identity_resolver",
            "sdk_ua_app_id",
            "user_agent_extra",
            "interceptors",
            "http_request_config",
            "transport",
            "retry_strategy",
            "endpoint_resolver",
            "protocol",
            "auth_schemes",
            "auth_scheme_resolver");

    @Override
    public Optional<ConfigBackend> configBackend(GenerationContext context) {
        if (!CodegenUtils.isAwsService(context.settings(), context.model())) {
            return Optional.empty();
        }
        return Optional.of(new AwsConfigBackend(context));
    }

    private static final class AwsConfigBackend implements ConfigBackend {
        private final GenerationContext context;

        AwsConfigBackend(GenerationContext context) {
            this.context = context;
        }

        private static Symbol awsConfig(String name) {
            return Symbol.builder()
                    .name(name)
                    .namespace("smithy_aws_core.config.aws_config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
        }

        @Override
        public Symbol baseSymbol() {
            return awsConfig("AwsConfigBase");
        }

        @Override
        public Symbol syncConfigSymbol() {
            return awsConfig("AwsConfig");
        }

        @Override
        public Symbol asyncConfigSymbol() {
            return awsConfig("AsyncAwsConfig");
        }

        @Override
        public Symbol overridesBaseSymbol() {
            return Symbol.builder()
                    .name("AwsConfigOverrides")
                    .namespace("smithy_aws_core.config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
        }

        @Override
        public boolean isPredefinedField(String name) {
            return PREDEFINED_CONFIG_FIELDS.contains(name);
        }

        @Override
        public List<ResolveParam> resolveParams() {
            var fileSystem = Symbol.builder()
                    .name("FileSystem")
                    .namespace("smithy_aws_core.config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var str = Symbol.builder().name("str").build();
            return List.of(
                    new ResolveParam("profile", str),
                    new ResolveParam("fs", fileSystem),
                    new ResolveParam("config_file_path", str),
                    new ResolveParam("credentials_file_path", str));
        }

        @Override
        public void writeExtraFields(GenerationContext context, PythonWriter writer) {
            var fieldSpecSymbol = Symbol.builder()
                    .name("FieldSpec")
                    .namespace("smithy_core.config", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                    .build();
            var awsConfigBaseSymbol = awsConfig("AwsConfigBase");
            var service = context.settings().service(context.model());
            var serviceIndex = software.amazon.smithy.model.knowledge.ServiceIndex.of(context.model());
            var hasAuth = !serviceIndex.getAuthSchemes(service).isEmpty();
            final String serviceId = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElse(service.getId().getName());

            // Spread the AWS base fields first; everything below deliberately overrides
            // them and so must come after the spread.
            writer.write("**$T._FIELDS,", awsConfigBaseSymbol);

            // endpoint_uri — service-aware resolver.
            var endpointUriResolverSymbol = Symbol.builder()
                    .name("EndpointUriResolver")
                    .namespace("smithy_aws_core.config.resolvers", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var snakeCaseServiceId = serviceId.replace(" ", "_").toLowerCase();
            writer.write("\"endpoint_uri\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default=None,");
            writer.write("resolver=$T($S),", endpointUriResolverSymbol, snakeCaseServiceId);
            writer.write("async_resolver=$T($S).resolve_async,", endpointUriResolverSymbol, snakeCaseServiceId);
            writer.dedent();
            writer.write("),");

            // endpoint_resolver.
            var endpointPrefix = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getEndpointPrefix)
                    .orElse(service.getId().getName());
            writer.write("\"endpoint_resolver\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: $T(endpoint_prefix=$S),",
                    AwsRuntimeTypes.STANDARD_REGIONAL_ENDPOINTS_RESOLVER,
                    endpointPrefix);
            writer.dedent();
            writer.write("),");

            // protocol.
            writer.write("\"protocol\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: ${C|},",
                    writer.consumer(w -> context.protocolGenerator().initializeSyncProtocol(context, w)));
            writer.write("async_default_factory=lambda: ${C|},",
                    writer.consumer(w -> context.protocolGenerator().initializeProtocol(context, w)));
            writer.write("converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,");
            writer.dedent();
            writer.write("),");

            // auth.
            if (hasAuth) {
                writer.write("\"auth_schemes\": $T(", fieldSpecSymbol);
                writer.indent();
                writer.write("default_factory=lambda: ${C|},",
                        writer.consumer(w -> writeDefaultAuthSchemes(context, w, true)));
                writer.write("async_default_factory=lambda: ${C|},",
                        writer.consumer(w -> writeDefaultAuthSchemes(context, w, false)));
                writer.dedent();
                writer.write("),");

                writer.write("\"auth_scheme_resolver\": $T(", fieldSpecSymbol);
                writer.indent();
                writer.write("default_factory=$T,",
                        CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings()));
                writer.dedent();
                writer.write("),");
            }

            // transport.
            writer.write("\"transport\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("urllib3"));
            writer.write("default_factory=lambda: $T(),", RuntimeTypes.URLLIB3_CLIENT);
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
            writer.write("async_default_factory=lambda: $T(),", RuntimeTypes.AIOHTTP_CLIENT);
            writer.dedent();
            writer.write("),");
        }

        private static void writeDefaultAuthSchemes(GenerationContext context, PythonWriter writer, boolean sync) {
            var service = context.settings().service(context.model());
            writer.openBlock("{");
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                    if (plugin.matchesService(context.model(), service) && plugin.getAuthScheme().isPresent()) {
                        var scheme = plugin.getAuthScheme().get();
                        writer.write("$T($S): ${C|},",
                                RuntimeTypes.SHAPE_ID,
                                scheme.getAuthTrait(),
                                writer.consumer(w -> {
                                    if (sync) {
                                        scheme.initializeSyncScheme(context, w, service);
                                    } else {
                                        scheme.initializeScheme(context, w, service);
                                    }
                                }));
                    }
                }
            }
            writer.closeBlock("}");
        }
    }
}
