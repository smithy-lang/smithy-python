/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsConfiguration.REGION;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.pattern.UriPattern;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.HttpTrait;
import software.amazon.smithy.model.transform.ModelTransformer;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.EndpointTestGenerator;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.integrations.EndpointRulesExtension;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.rulesengine.language.syntax.expressions.Expression;
import software.amazon.smithy.rulesengine.language.syntax.expressions.functions.LibraryFunction;
import software.amazon.smithy.rulesengine.language.syntax.parameters.Parameter;
import software.amazon.smithy.rulesengine.language.syntax.rule.Condition;
import software.amazon.smithy.rulesengine.traits.ContextParamTrait;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds the region config property and registers the AWS rules extension for AWS services
 * and for services whose endpoint rules use AWS functions or built-ins. In generated
 * endpoint tests, the extension sets the AWS built-ins and test credentials. For S3, it
 * strips the bucket from the operation URIs because the rules place it.
 */
@SmithyInternalApi
public final class AwsEndpointRulesIntegration implements PythonIntegration {
    /**
     * The config fields the AWS rules extension binds built-ins to, besides the base
     * region field, by built-in. A service's config gets a field for each one its rules
     * declare. Keep in sync with {@code AWS_RULES_EXTENSION} in smithy_aws_core.endpoints.
     */
    static final Map<String, BuiltInField> BUILT_IN_FIELDS = Map.of(
            "AWS::UseFIPS",
            new BuiltInField("use_fips_endpoint",
                    null,
                    resolver("resolve_use_fips_endpoint"),
                    null),
            "AWS::UseDualStack",
            new BuiltInField("use_dualstack_endpoint",
                    null,
                    resolver("resolve_use_dualstack_endpoint"),
                    null),
            // The SDKs and Tools Reference Guide default.
            "AWS::Auth::AccountIdEndpointMode",
            new BuiltInField("account_id_endpoint_mode",
                    "preferred",
                    resolver("resolve_account_id_endpoint_mode"),
                    validator("validate_account_id_endpoint_mode")));
    private static final String REGION_BUILT_IN = "AWS::Region";
    private static final String ACCOUNT_ID = "AWS::Auth::AccountId";
    private static final String TEST_ACCESS_KEY_ID = "test-access-key-id";
    private static final String TEST_SECRET_ACCESS_KEY = "test-secret-access-key";
    private static final String S3_SDK_ID = "S3";
    private static final String BUCKET = "Bucket";
    private static final String BUCKET_LABEL = "/{" + BUCKET + "}";

    /**
     * Strips the leading {@code /{Bucket}} from S3's operation URIs. S3's rules place the
     * bucket in the endpoint host or path, so a serialized path that also starts with the
     * bucket would send it twice. The {@code Bucket} member keeps its {@code @httpLabel},
     * so it isn't serialized into the body; the path serializer ignores a label that isn't
     * in the URI.
     */
    @Override
    public Model preprocessModel(Model model, PythonSettings settings) {
        var service = settings.service(model);
        if (!service.getTrait(ServiceTrait.class).map(ServiceTrait::getSdkId).orElse("").equals(S3_SDK_ID)) {
            return model;
        }
        var replaced = new ArrayList<Shape>();
        for (OperationShape operation : TopDownIndex.of(model).getContainedOperations(service)) {
            var http = operation.getTrait(HttpTrait.class);
            if (http.isPresent() && placesBucket(model, operation, http.get())) {
                var uri = http.get().getUri().toString().substring(BUCKET_LABEL.length());
                if (uri.isEmpty() || uri.startsWith("?")) {
                    uri = "/" + uri;
                }
                replaced.add(operation.toBuilder()
                        .addTrait(http.get().toBuilder().uri(UriPattern.parse(uri)).build())
                        .build());
            }
        }
        return ModelTransformer.create().replaceShapes(model, replaced);
    }

    // Whether the URI starts with the Bucket label and the rules read Bucket.
    private static boolean placesBucket(Model model, OperationShape operation, HttpTrait http) {
        var uri = http.getUri().toString();
        if (!uri.equals(BUCKET_LABEL) && !uri.startsWith(BUCKET_LABEL + "/") && !uri.startsWith(BUCKET_LABEL + "?")) {
            return false;
        }
        return model.expectShape(operation.getInputShape())
                .getMember(BUCKET)
                .filter(member -> member.hasTrait(ContextParamTrait.class))
                .isPresent();
    }

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var plugins = new ArrayList<RuntimeClientPlugin>();
        if (context.applicationProtocol().isHttpProtocol()) {
            plugins.add(RuntimeClientPlugin.builder()
                    .addConfigProperty(REGION)
                    .build());
        }
        plugins.add(RuntimeClientPlugin.builder()
                .servicePredicate((model, service) -> service.hasTrait(ServiceTrait.class) || usesAwsRules(service))
                .endpointRulesExtension(new AwsRulesExtension())
                .build());
        return plugins;
    }

    /**
     * A config field that the AWS rules extension binds a built-in to.
     *
     * @param name the config field name.
     * @param defaultValue the field's default, or null for None.
     * @param resolver writes the expression that resolves the field from the environment
     *     and profile.
     * @param validator the function that validates the field's value, or null for none.
     */
    record BuiltInField(String name, String defaultValue, Consumer<PythonWriter> resolver, Symbol validator) {}

    private static Consumer<PythonWriter> resolver(String name) {
        var symbol = Symbol.builder()
                .name(name)
                .namespace("smithy_aws_core.aio.config.resolvers", ".")
                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                .build();
        return writer -> writer.writeInline("$T", symbol);
    }

    private static Symbol validator(String name) {
        return Symbol.builder()
                .name(name)
                .namespace("smithy_aws_core.config.validators", ".")
                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                .build();
    }

    /**
     * Whether a service's endpoint rules call AWS functions or read AWS built-ins.
     *
     * @param service the service.
     * @return true if the rules need the AWS rules extension.
     */
    static boolean usesAwsRules(ServiceShape service) {
        var trait = service.getTrait(EndpointBddTrait.class);
        if (trait.isEmpty()) {
            return false;
        }
        for (Parameter parameter : trait.get().getParameters()) {
            if (parameter.getBuiltIn().filter(b -> b.startsWith("AWS::")).isPresent()) {
                return true;
            }
        }
        for (Condition condition : trait.get().getConditions()) {
            if (callsAwsFunction(condition.getFunction())) {
                return true;
            }
        }
        return false;
    }

    private static boolean callsAwsFunction(Expression expression) {
        if (expression instanceof LibraryFunction function) {
            if (function.getName().startsWith("aws.")) {
                return true;
            }
            for (Expression argument : function.getArguments()) {
                if (callsAwsFunction(argument)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static final class AwsRulesExtension implements EndpointRulesExtension {

        @Override
        public Symbol getRulesExtensionSymbol(GenerationContext context) {
            return AwsRuntimeTypes.AWS_RULES_EXTENSION;
        }

        @Override
        public void writeEndpointTestConfig(GenerationContext context, PythonWriter writer) {
            if (CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model()).isEmpty()) {
                return;
            }
            // Config resolution requires a region. Explicit values keep endpoint_uri, the
            // credentials and the built-in fields from being read from the environment.
            writer.write("""
                    "region": "us-east-1",
                    "endpoint_uri": None,
                    "aws_credentials_identity_resolver": $T($T(access_key_id=$S, secret_access_key=$S)),""",
                    RuntimeTypes.STATIC_CREDENTIALS_RESOLVER,
                    AwsRuntimeTypes.AWS_CREDENTIALS_IDENTITY,
                    TEST_ACCESS_KEY_ID,
                    TEST_SECRET_ACCESS_KEY);
            var service = context.settings().service(context.model());
            service.getTrait(EndpointBddTrait.class).ifPresent(trait -> {
                for (Parameter parameter : trait.getParameters()) {
                    parameter.getBuiltIn().map(BUILT_IN_FIELDS::get).ifPresent(field -> {
                        if (field.defaultValue() == null) {
                            writer.write("$S: None,", field.name());
                        } else {
                            writer.write("$S: $S,", field.name(), field.defaultValue());
                        }
                    });
                }
            });
        }

        @Override
        public Optional<Consumer<PythonWriter>> getEndpointTestBuiltIn(
                GenerationContext context,
                String builtIn,
                Node value
        ) {
            if (CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model()).isEmpty()) {
                return Optional.empty();
            }
            var field = builtIn.equals(REGION_BUILT_IN)
                    ? REGION.name()
                    : Optional.ofNullable(BUILT_IN_FIELDS.get(builtIn)).map(BuiltInField::name).orElse(null);
            if (field != null) {
                return Optional.of(writer -> writer.write("$S: $L,", field, EndpointTestGenerator.literal(value)));
            }
            // The account ID is read from the identity, so the test credentials carry it.
            if (builtIn.equals(ACCOUNT_ID)) {
                return Optional
                        .of(writer -> writer.write(
                                "$S: $T($T(access_key_id=$S, secret_access_key=$S, account_id=$S)),",
                                "aws_credentials_identity_resolver",
                                RuntimeTypes.STATIC_CREDENTIALS_RESOLVER,
                                AwsRuntimeTypes.AWS_CREDENTIALS_IDENTITY,
                                TEST_ACCESS_KEY_ID,
                                TEST_SECRET_ACCESS_KEY,
                                value.expectStringNode().getValue()));
            }
            return Optional.empty();
        }
    }
}
