/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
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
            var maybeAsyncPluginSymbol = CodegenUtils.getAsyncPluginSymbol(context.settings(), model);
            if (maybeAsyncConfigSymbol.isEmpty() || maybeAsyncPluginSymbol.isEmpty()) {
                return;
            }
            var asyncConfigSymbol = maybeAsyncConfigSymbol.get();
            var asyncPluginSymbol = maybeAsyncPluginSymbol.get();

            final String serviceId = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElse(context.settings().service().getName());

            // Import AsyncAwsConfig base class
            var asyncAwsConfigSymbol = Symbol.builder()
                    .name("AsyncAwsConfig")
                    .namespace("smithy_aws_core.config.aws_config", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();

            // Import FieldSpec and ClassVar
            var fieldSpecSymbol = Symbol.builder()
                    .name("FieldSpec")
                    .namespace("smithy_aws_core.config.types", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            writer.addStdlibImport("typing", "ClassVar");
            writer.addStdlibImport("typing", "Any");
            writer.addStdlibImport("dataclasses", "dataclass");

            writer.write("");
            writer.write("");
            // repr=False is required: AsyncAwsConfig defines a __repr__ that filters out
            // credential fields, and a generated __repr__ on this subclass would shadow it
            // and leak secrets.
            writer.write("@dataclass(kw_only=True, repr=False)");
            writer.openBlock("class $L($T):", asyncConfigSymbol.getName(), asyncAwsConfigSymbol);
            writer.writeDocs(serviceId + " configuration (async-resolved).", context);
            writer.write("");

            // Write service-specific field declarations
            writer.write("endpoint_resolver: $T | None = None", RuntimeTypes.ENDPOINT_RESOLVER);
            writer.writeDocs("The endpoint resolver used to resolve the final endpoint per-operation "
                    + "based on the configuration.", context);
            writer.write("");

            writer.write("protocol: $T | None = None",
                    Symbol.builder()
                            .name("ClientProtocol[Any, Any]")
                            .addReference(Symbol.builder()
                                    .name("ClientProtocol")
                                    .namespace("smithy_core.aio.interfaces", ".")
                                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                    .build())
                            .build());
            writer.writeDocs("The protocol to serialize and deserialize requests with.", context);
            writer.write("");

            var serviceIndex = ServiceIndex.of(context.model());
            var hasAuth = !serviceIndex.getAuthSchemes(context.settings().service()).isEmpty();

            if (hasAuth) {
                writer.write("auth_schemes: dict[$T, $T] | None = None",
                        RuntimeTypes.SHAPE_ID,
                        Symbol.builder()
                                .name("AuthScheme[Any, Any, Any, Any]")
                                .addReference(Symbol.builder()
                                        .name("AuthScheme")
                                        .namespace("smithy_core.aio.interfaces.auth", ".")
                                        .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                        .build())
                                .build());
                writer.writeDocs("A map of auth scheme ids to auth schemes.", context);
                writer.write("");

                writer.write("auth_scheme_resolver: $T | None = None",
                        CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings()));
                writer.writeDocs("An auth scheme resolver that determines the auth scheme "
                        + "for each operation.", context);
                writer.write("");
            }

            // Plugin-contributed field declarations (e.g., api_key for @httpApiKeyAuth).
            //
            // More than one plugin can contribute the same property — region, for
            // instance, comes from both the auth and regional-endpoints integrations
            // — so track the names already written and emit each only once.
            var writtenProperties = new LinkedHashSet<String>();
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                    if (plugin.matchesService(model, service)) {
                        for (ConfigProperty property : plugin.getConfigProperties()) {
                            if (!writtenProperties.add(property.name())) {
                                continue;
                            }
                            writer.write("$L: $T | None = None", property.name(), property.type());
                            writer.writeDocs(property.documentation(), context);
                            writer.write("");
                        }
                    }
                }
            }

            // Write _FIELDS class variable with service-specific defaults
            writer.openBlock("_FIELDS: ClassVar[dict[str, $T]] = {", fieldSpecSymbol);

            // Plugin-contributed FieldSpec entries.
            //
            // These are written *before* the base class spread on purpose. Plugins
            // declare config properties for the legacy Config object, which has no
            // base class, so some of them duplicate fields AsyncAwsConfig already
            // owns and resolves (region, credentials, sdk_ua_app_id, ...). Emitting
            // them first means the spread below wins for any such duplicate, so a
            // bare FieldSpec(default=None) can never clobber a base spec that
            // carries a resolver or validator. Properties the base doesn't declare
            // (e.g. api_key for @httpApiKeyAuth) survive untouched.
            //
            // Reuse the set collected above so these entries stay in step with the
            // field declarations and duplicate contributions are written once.
            for (String propertyName : writtenProperties) {
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
            writer.closeBlock("");

            // Generate the async plugin type alias
            writer.addStdlibImport("typing", "Callable");
            writer.addStdlibImport("typing", "TypeAlias");
            writer.write("");
            writer.write("");
            writer.write("$L: TypeAlias = Callable[[$L], None]",
                    asyncPluginSymbol.getName(),
                    asyncConfigSymbol.getName());
            writer.writeDocs(
                    "A callable that allows customizing the async config object on each request.",
                    context);
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
