/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.AsyncConfigSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * AWS integration that generates the async config subclass (e.g., AsyncBedrockRuntimeConfig)
 * inheriting from AsyncAwsConfig with service-specific fields and defaults.
 */
@SmithyInternalApi
public class AwsAsyncConfigIntegration implements PythonIntegration {
    // Fields the overrides TypedDict already gets from its base or from this file, so a
    // same-named plugin ConfigProperty must not be re-emitted (see pluginProperties loop).
    // Hand-synced, no cross-language guard: the base fields mirror AwsConfigOverrides /
    // AsyncAwsConfig._FIELDS in smithy-aws-core's config/aws_config.py (update here when
    // those change); the last four are the codegen-managed fields written below.
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
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        return List.of(new AsyncConfigInterceptor(context));
    }

    private static final class AsyncConfigInterceptor
            implements CodeInterceptor<AsyncConfigSection, PythonWriter> {

        private final GenerationContext context;

        AsyncConfigInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<AsyncConfigSection> sectionType() {
            return AsyncConfigSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, AsyncConfigSection section) {
            // Write any previous content first
            writer.write(previousText);

            var model = context.model();
            var service = context.settings().service(model);

            // Gate on the same source of truth the core generators use to decide whether
            // to emit references to these classes. If it says no symbol is generated, we
            // must not define one, or the two would disagree.
            var maybeAsyncConfigSymbol = CodegenUtils.getAsyncConfigSymbol(context.settings(), model);
            if (maybeAsyncConfigSymbol.isEmpty()) {
                return;
            }
            var asyncConfigSymbol = maybeAsyncConfigSymbol.get();

            final String serviceId = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElse(context.settings().service().getName());

            var serviceIndex = ServiceIndex.of(context.model());
            var hasAuth = !serviceIndex.getAuthSchemes(context.settings().service()).isEmpty();
            // Multiple plugins can contribute the same property. Preserve the first
            // declaration, matching the previous generated field behavior.
            var pluginProperties = new LinkedHashMap<String, ConfigProperty>();
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                    if (plugin.matchesService(model, service)) {
                        for (ConfigProperty property : plugin.getConfigProperties()) {
                            pluginProperties.putIfAbsent(property.name(), property);
                        }
                    }
                }
            }

            var asyncAwsConfigSymbol = Symbol.builder()
                    .name("AsyncAwsConfig")
                    .namespace("smithy_aws_core.config.aws_config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var awsConfigOverridesSymbol = Symbol.builder()
                    .name("AwsConfigOverrides")
                    .namespace("smithy_aws_core.config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var fileSystemSymbol = Symbol.builder()
                    .name("FileSystem")
                    .namespace("smithy_aws_core.config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var fieldSpecSymbol = Symbol.builder()
                    .name("FieldSpec")
                    .namespace("smithy_aws_core.config.types", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var protocolSymbol = Symbol.builder()
                    .name("ClientProtocol[Any, Any]")
                    .addReference(Symbol.builder()
                            .name("ClientProtocol")
                            .namespace("smithy_core.aio.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build();
            var authSchemeSymbol = Symbol.builder()
                    .name("AuthScheme[Any, Any, Any, Any]")
                    .addReference(Symbol.builder()
                            .name("AuthScheme")
                            .namespace("smithy_core.aio.interfaces.auth", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build();
            var authSchemeResolverSymbol = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());
            var overridesTypeName = "_" + asyncConfigSymbol.getName() + "Overrides";

            writer.addStdlibImport("typing", "ClassVar");
            writer.addStdlibImport("typing", "Any");
            writer.addStdlibImport("typing", "Self");
            writer.addStdlibImport("typing", "Unpack");
            writer.addStdlibImport("dataclasses", "dataclass");
            writer.addStdlibImport("dataclasses", "field");

            writer.write("");
            writer.write("");
            writer.openBlock("class $L($T, total=False):", overridesTypeName, awsConfigOverridesSymbol);
            writer.write("endpoint_resolver: $T | None", RuntimeTypes.ENDPOINT_RESOLVER);
            writer.write("protocol: $T | None", protocolSymbol);
            if (hasAuth) {
                writer.write("auth_schemes: dict[$T, $T] | None",
                        RuntimeTypes.SHAPE_ID,
                        authSchemeSymbol);
                writer.write("auth_scheme_resolver: $T | None", authSchemeResolverSymbol);
            }
            for (ConfigProperty property : pluginProperties.values()) {
                if (!PREDEFINED_CONFIG_FIELDS.contains(property.name())) {
                    // Always nullable to match the dataclass field and FieldSpec below,
                    // both of which are unconditionally "<T> | None = None".
                    writer.write("$L: $T | None", property.name(), property.type());
                }
            }
            writer.closeBlock("");
            writer.write("");

            // repr=False is required: AsyncAwsConfig defines a __repr__ that filters out
            // credential fields, and a generated __repr__ on this subclass would shadow it
            // and leak secrets.
            writer.write("@dataclass(kw_only=True, repr=False, init=False)");
            writer.openBlock("class $L($T):", asyncConfigSymbol.getName(), asyncAwsConfigSymbol);
            writer.writeDocs(serviceId + " configuration (async-resolved).", context);
            writer.write("");

            // Write service-specific field declarations
            writer.write("endpoint_resolver: $T | None = None", RuntimeTypes.ENDPOINT_RESOLVER);
            writer.writeDocs("The endpoint resolver used to resolve the final endpoint per-operation "
                    + "based on the configuration.", context);
            writer.write("");

            writer.write("protocol: $T | None = None", protocolSymbol);
            writer.writeDocs("The protocol to serialize and deserialize requests with.", context);
            writer.write("");

            writer.write("interceptors: list[_ServiceInterceptor] = field(default_factory=lambda: [])");
            writer.writeDocs(
                    "The list of interceptors, which are hooks that are called during the execution of a request.",
                    context);
            writer.write("");

            if (hasAuth) {
                writer.write("auth_schemes: dict[$T, $T] | None = None",
                        RuntimeTypes.SHAPE_ID,
                        authSchemeSymbol);
                writer.writeDocs("A map of auth scheme ids to auth schemes.", context);
                writer.write("");

                writer.write("auth_scheme_resolver: $T | None = None", authSchemeResolverSymbol);
                writer.writeDocs("An auth scheme resolver that determines the auth scheme "
                        + "for each operation.", context);
                writer.write("");
            }

            // Plugin-contributed field declarations (e.g., api_key for @httpApiKeyAuth).
            for (ConfigProperty property : pluginProperties.values()) {
                writer.write("$L: $T | None = None", property.name(), property.type());
                writer.writeDocs(property.documentation(), context);
                writer.write("");
            }

            // Write _FIELDS class variable with service-specific defaults
            writer.openBlock("_FIELDS: ClassVar[dict[str, $T]] = {", fieldSpecSymbol);

            // Plugin-contributed FieldSpec entries are emitted before the base class
            // spread. Some duplicate fields already in AsyncAwsConfig._FIELDS (e.g.,
            // region, sdk_ua_app_id) — these are harmlessly overwritten by the spread
            // below. Fields unique to this service (e.g., api_key from @httpApiKeyAuth)
            // survive and participate in the resolution pipeline.
            for (String propertyName : pluginProperties.keySet()) {
                writer.write("\"$L\": $T(default=None),", propertyName, fieldSpecSymbol);
            }

            writer.write("**$T._FIELDS,", asyncAwsConfigSymbol);

            // Everything below deliberately overrides the base class and so must
            // stay after the spread.

            // endpoint_uri FieldSpec — overrides base class with service-aware resolver
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
            writer.dedent();
            writer.write("),");

            // endpoint_resolver FieldSpec
            var endpointPrefix = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getEndpointPrefix)
                    .orElse(context.settings().service().getName());
            writer.write("\"endpoint_resolver\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: $T(endpoint_prefix=$S),",
                    AwsRuntimeTypes.STANDARD_REGIONAL_ENDPOINTS_RESOLVER,
                    endpointPrefix);
            writer.dedent();
            writer.write("),");

            // protocol FieldSpec
            writer.write("\"protocol\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: ${C|},",
                    writer.consumer(w -> context.protocolGenerator().initializeProtocol(context, w)));
            writer.dedent();
            writer.write("),");

            // auth_schemes FieldSpec
            if (hasAuth) {
                writer.write("\"auth_schemes\": $T(", fieldSpecSymbol);
                writer.indent();
                writer.write("default_factory=lambda: ${C|},",
                        writer.consumer(w -> writeAsyncDefaultAuthSchemes(context, w)));
                writer.dedent();
                writer.write("),");

                // auth_scheme_resolver FieldSpec
                writer.write("\"auth_scheme_resolver\": $T(", fieldSpecSymbol);
                writer.indent();
                writer.write("default_factory=$T,",
                        CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings()));
                writer.dedent();
                writer.write("),");
            }

            // transport FieldSpec
            writer.write("\"transport\": $T(", fieldSpecSymbol);
            writer.indent();
            if (usesHttp2(context)) {
                writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("awscrt"));
                writer.write("default_factory=lambda: $T(),", RuntimeTypes.AWS_CRT_HTTP_CLIENT);
            } else {
                writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
                writer.write("default_factory=lambda: $T(),", RuntimeTypes.AIOHTTP_CLIENT);
            }
            writer.dedent();
            writer.write("),");

            writer.closeBlock("}");
            writer.write("");
            if (hasAuth) {
                writer.write("def set_auth_scheme(self, scheme: $T) -> None:", authSchemeSymbol);
                writer.indent();
                writer.writeDocs("""
                        Set an auth scheme implementation using its scheme ID.

                        :param scheme: The auth scheme to add or replace.
                        """, context);
                writer.write("auth_schemes = dict(self.auth_schemes or {})");
                writer.write("auth_schemes[scheme.scheme_id] = scheme");
                writer.write("self.auth_schemes = auth_schemes");
                writer.dedent();
                writer.write("");
            }
            writer.write("@classmethod");
            writer.write("async def resolve(  # pyright: ignore[reportIncompatibleMethodOverride]");
            writer.indent();
            writer.write("cls,");
            writer.write("*,");
            writer.write("profile: str | None = None,");
            writer.write("fs: $T | None = None,", fileSystemSymbol);
            writer.write("config_file_path: str | None = None,");
            writer.write("credentials_file_path: str | None = None,");
            writer.write("**overrides: Unpack[$L],", overridesTypeName);
            writer.dedent();
            writer.write(") -> Self:");
            writer.indent();
            writer.writeDocs(
                    "Resolve config from environment, config files, defaults, and explicit overrides.",
                    context);
            writer.write("return await cls._resolve(");
            writer.indent();
            writer.write("profile=profile,");
            writer.write("fs=fs,");
            writer.write("config_file_path=config_file_path,");
            writer.write("credentials_file_path=credentials_file_path,");
            writer.write("overrides=overrides,");
            writer.dedent();
            writer.write(")");
            writer.dedent();
            writer.closeBlock("");
        }

        private static void writeAsyncDefaultAuthSchemes(GenerationContext context, PythonWriter writer) {
            var service = context.settings().service(context.model());
            writer.openBlock("{");
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                    if (plugin.matchesService(context.model(), service) && plugin.getAuthScheme().isPresent()) {
                        var scheme = plugin.getAuthScheme().get();
                        writer.write("$T($S): ${C|},",
                                RuntimeTypes.SHAPE_ID,
                                scheme.getAuthTrait(),
                                writer.consumer(w -> scheme.initializeScheme(context, writer, service)));
                    }
                }
            }
            writer.closeBlock("}");
        }

        private static boolean usesHttp2(GenerationContext context) {
            var configuration = context.applicationProtocol().configuration();
            var httpVersions = configuration.getArrayMember("http")
                    .orElse(ArrayNode.arrayNode())
                    .getElementsAs(StringNode.class)
                    .stream()
                    .map(node -> node.getValue().toLowerCase(Locale.ENGLISH))
                    .toList();

            if (httpVersions.contains("h2")) {
                return true;
            }

            var eventIndex = EventStreamIndex.of(context.model());
            var topDownIndex = TopDownIndex.of(context.model());
            for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().service())) {
                if (eventIndex.getInputInfo(operation).isPresent()
                        || eventIndex.getOutputInfo(operation).isPresent()) {
                    return true;
                }
            }

            return false;
        }
    }
}
