/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsEndpointRulesIntegration.BUILT_IN_FIELDS;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Set;
import java.util.function.UnaryOperator;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.python.aws.codegen.AwsEndpointRulesIntegration.BuiltInField;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SyncVariant;
import software.amazon.smithy.python.codegen.generators.ConfigGenerator;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.AsyncConfigSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.rulesengine.language.syntax.parameters.Parameter;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * AWS integration that generates the async config subclass (e.g., AsyncBedrockRuntimeConfig)
 * inheriting from AsyncAwsConfig with service-specific fields and defaults.
 */
@SmithyInternalApi
public class AwsAsyncConfigIntegration implements PythonIntegration {
    // Keep base fields synchronized with AwsConfigOverrides. The remaining fields are
    // generated explicitly below.
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

    // The service's endpoint rules parameters, in trait order.
    private static List<Parameter> endpointParameters(ServiceShape service) {
        var parameters = new ArrayList<Parameter>();
        service.getTrait(EndpointBddTrait.class).ifPresent(trait -> trait.getParameters().forEach(parameters::add));
        return parameters;
    }

    // A built-in's config field, typed and documented by its rules parameter.
    private static ConfigProperty builtInProperty(Parameter parameter, BuiltInField field) {
        var type = switch (parameter.getType()) {
            case BOOLEAN -> "bool";
            case STRING -> "str";
            default -> throw new CodegenException(String.format(
                    "Unsupported type %s for built-in %s",
                    parameter.getType(),
                    parameter.getBuiltIn().orElseThrow()));
        };
        var documentation = parameter.getDocumentation()
                .orElse("The " + parameter.getName() + " endpoint parameter.");
        if (field.defaultValue() != null) {
            documentation += " Defaults to " + field.defaultValue() + ".";
        }
        return ConfigProperty.builder()
                .name(field.name())
                .type(Symbol.builder().name(type).build())
                .documentation(documentation)
                .resolver(field.resolver())
                .validator(field.validator())
                .build();
    }

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

            var asyncConfigSymbol = CodegenUtils.getAsyncConfigSymbol(context.settings(), model);
            var sync = section.sync();
            UnaryOperator<String> code = sync ? SyncVariant::toSyncCode : UnaryOperator.identity();
            var configName = sync
                    ? SyncVariant.toSyncName(asyncConfigSymbol.getName())
                    : asyncConfigSymbol.getName();

            final String serviceId = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElse(context.settings().service().getName());

            var serviceIndex = ServiceIndex.of(context.model());
            var hasAuth = !serviceIndex.getAuthSchemes(context.settings().service()).isEmpty();
            // Preserve the first declaration when plugins contribute duplicate properties.
            var pluginProperties = new LinkedHashMap<String, ConfigProperty>();
            for (ConfigProperty property : ConfigGenerator.clientContextProperties(context)) {
                pluginProperties.putIfAbsent(property.name(), property);
            }
            // A field for each built-in the rules declare that the AWS rules extension binds
            // to config, and the non-None defaults of those fields by name.
            var builtInDefaults = new HashMap<String, String>();
            for (Parameter parameter : endpointParameters(service)) {
                var field = parameter.getBuiltIn().map(BUILT_IN_FIELDS::get).orElse(null);
                if (field != null
                        && pluginProperties.putIfAbsent(field.name(), builtInProperty(parameter, field)) == null
                        && field.defaultValue() != null) {
                    builtInDefaults.put(field.name(), field.defaultValue());
                }
            }
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
                    .namespace("smithy_aws_core.aio.config.aws_config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var awsConfigOverridesSymbol = Symbol.builder()
                    .name("AsyncAwsConfigOverrides")
                    .namespace("smithy_aws_core.aio.config.aws_config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            var fileSystemSymbol = Symbol.builder()
                    .name("AsyncFileSystem")
                    .namespace("smithy_aws_core.aio.config.filesystem", ".")
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
                            .namespace("smithy_core.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build();
            // The override accepts a protocol class in addition to an instance; the
            // resolved dataclass field is always an instance, so it uses protocolSymbol.
            var protocolInputSymbol = Symbol.builder()
                    .name("ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]]")
                    .addReference(Symbol.builder()
                            .name("ClientProtocol")
                            .namespace("smithy_core.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .addReference(Symbol.builder()
                            .name("ProtocolConstructor")
                            .namespace("smithy_core.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build();
            var authSchemeSymbol = Symbol.builder()
                    .name("AsyncAuthScheme[Any, Any, Any, Any]")
                    .addReference(Symbol.builder()
                            .name("AsyncAuthScheme")
                            .namespace("smithy_core.aio.interfaces.auth", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .build();
            // The declared field/override type is the protocol so any conforming resolver
            // is accepted without subclassing the generated default.
            var authSchemeResolverInterfaceSymbol = Symbol.builder()
                    .name("AuthSchemeResolver")
                    .namespace("smithy_core.interfaces.auth", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                    .build();
            var overridesTypeName = "_" + configName + "Overrides";

            writer.addStdlibImport("typing", "ClassVar");
            writer.addStdlibImport("typing", "Any");
            writer.addStdlibImport("typing", "Self");
            writer.addStdlibImport("typing", "Unpack");
            writer.addStdlibImport("dataclasses", "dataclass");
            writer.addStdlibImport("dataclasses", "field");

            writer.write("");
            writer.write("");
            // The config class refers to these when it is created, so they come first.
            for (ConfigProperty property : pluginProperties.values()) {
                property.definitions().ifPresent(definitions -> {
                    definitions.accept(writer);
                    writer.write("");
                    writer.write("");
                });
            }
            writer.openBlock("class $L($T, total=False):", overridesTypeName, awsConfigOverridesSymbol);
            writer.write("endpoint_resolver: $T | None", RuntimeTypes.CONFIG_ENDPOINT_RESOLVER);
            writer.write("protocol: $T | None", protocolInputSymbol);
            if (hasAuth) {
                writer.write("auth_schemes: dict[$T, $T] | None",
                        RuntimeTypes.SHAPE_ID,
                        authSchemeSymbol);
                writer.write("auth_scheme_resolver: $T | None", authSchemeResolverInterfaceSymbol);
            }
            for (ConfigProperty property : pluginProperties.values()) {
                if (!PREDEFINED_CONFIG_FIELDS.contains(property.name())) {
                    // Match the nullable dataclass field and FieldSpec below.
                    writer.write("$L: $T | None", property.name(), property.type());
                }
            }
            writer.closeBlock("");
            writer.write("");

            // repr=False is required: AsyncAwsConfig defines a __repr__ that filters out
            // credential fields, and a generated __repr__ on this subclass would shadow it
            // and leak secrets.
            writer.write("@dataclass(kw_only=True, repr=False, init=False)");
            writer.openBlock("class $L($T):", configName, asyncAwsConfigSymbol);
            writer.writeDocs(serviceId + (sync ? " configuration." : " configuration (async-resolved)."), context);
            writer.write("");

            // Write service-specific field declarations
            writer.write("endpoint_resolver: $T | None = None", RuntimeTypes.CONFIG_ENDPOINT_RESOLVER);
            writer.writeDocs("The endpoint resolver used to resolve the final endpoint per-operation "
                    + "based on the configuration.", context);
            writer.write("");

            writer.write("protocol: $T | None = None", protocolSymbol);
            var protocolDocs = "Pass a protocol class reference from smithy_aws_core.aio.protocols "
                    + "to select the protocol, e.g. protocol=AsyncAwsJson10ClientProtocol. For custom "
                    + "protocols a protocol instance may also be passed.";
            writer.writeDocs(sync
                    ? SyncVariant.toSyncName(protocolDocs.replace(".aio.", "."))
                    : protocolDocs, context);
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

                writer.write("auth_scheme_resolver: $T | None = None", authSchemeResolverInterfaceSymbol);
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
            for (ConfigProperty property : pluginProperties.values()) {
                var propertyName = property.name();
                var defaultValue = property.defaultValue().orElse(builtInDefaults.get(propertyName));
                if (defaultValue == null && property.resolver().isEmpty() && property.validator().isEmpty()) {
                    writer.write("\"$L\": $T(default=None),", propertyName, fieldSpecSymbol);
                    continue;
                }
                writer.write("\"$L\": $T(", propertyName, fieldSpecSymbol);
                writer.indent();
                if (defaultValue != null) {
                    writer.write("default=$S,", defaultValue);
                } else {
                    writer.write("default=None,");
                }
                property.resolver()
                        .ifPresent(resolver -> writer.write("resolver=$C,", (Runnable) () -> resolver.accept(writer)));
                property.validator().ifPresent(validator -> writer.write("validator=$T,", validator));
                writer.dedent();
                writer.write("),");
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
            writer.write("resolver=$T($S).program,", endpointUriResolverSymbol, snakeCaseServiceId);
            writer.dedent();
            writer.write("),");

            // endpoint_resolver FieldSpec
            writer.write("\"endpoint_resolver\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: $C,",
                    writer.consumer(w -> ConfigGenerator.writeDefaultEndpointResolver(context, w)));
            writer.dedent();
            writer.write("),");

            // protocol FieldSpec
            writer.write("\"protocol\": $T(", fieldSpecSymbol);
            writer.indent();
            writer.write("default_factory=lambda: ${C|},",
                    writer.consumer(w -> context.protocolGenerator().initializeProtocol(context, w)));
            writer.write("converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,");
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
            if (!sync) {
                writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
            }
            writer.write("default_factory=lambda: $T(),", RuntimeTypes.AIOHTTP_CLIENT);
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
            writer.write(code.apply("async def resolve(  # pyright: ignore[reportIncompatibleMethodOverride]"));
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
            writer.write(code.apply("return await cls._resolve("));
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

    }
}
