/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen.integration;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.BiPredicate;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Represents a runtime plugin for a client that hooks into various aspects
 * of Python code generation, including adding configuration settings
 * to clients and interceptors to both clients and commands.
 *
 * <p>These runtime client plugins are registered through the
 * {@link PythonIntegration} SPI and applied to the code generator at
 * build-time.
 */
@SmithyUnstableApi
public final class RuntimeClientPlugin implements ToSmithyBuilder<RuntimeClientPlugin> {

    private static final OperationPredicate OPERATION_ALWAYS_FALSE = (model, service, operation) -> false;

    private final BiPredicate<Model, ServiceShape> servicePredicate;
    private final OperationPredicate operationPredicate;
    private final List<ConfigProperty> configProperties;
    private final SymbolReference pythonPlugin;

    private final AuthScheme authScheme;

    private RuntimeClientPlugin(Builder builder) {
        servicePredicate = builder.servicePredicate;
        operationPredicate = builder.operationPredicate;
        configProperties = Collections.unmodifiableList(builder.configProperties);
        this.pythonPlugin = builder.pythonPlugin;
        this.authScheme = builder.authScheme;
    }

    /**
     * Predicate that tests whether a plugin should be applied to an individual operation.
     */
    @FunctionalInterface
    public interface OperationPredicate {
        /**
         * Tests if this should be applied to an individual operation.
         *
         * @param model     Model the operation belongs to.
         * @param service   Service the operation belongs to.
         * @param operation Operation to test.
         * @return Returns true if interceptors / plugins should be applied to the operation.
         */
        boolean test(Model model, ServiceShape service, OperationShape operation);
    }

    /**
     * Returns true if this plugin applies to the given service.
     *
     * <p>By default, a plugin applies to all services but not to specific
     * commands. You an configure a plugin to apply only to a subset of
     * services (for example, only apply to a known service or a service
     * with specific traits) or to no services at all (for example, if
     * the plugin is meant to by command-specific and not on every
     * command executed by the service).
     *
     * @param model   The model the service belongs to.
     * @param service Service shape to test against.
     * @return Returns true if the plugin is applied to the given service.
     * @see #matchesOperation(Model, ServiceShape, OperationShape)
     */
    public boolean matchesService(Model model, ServiceShape service) {
        return servicePredicate.test(model, service);
    }

    /**
     * Returns true if this plugin applies to the given operation.
     *
     * @param model     Model the operation belongs to.
     * @param service   Service the operation belongs to.
     * @param operation Operation to test against.
     * @return Returns true if the plugin is applied to the given operation.
     * @see #matchesService(Model, ServiceShape)
     */
    public boolean matchesOperation(Model model, ServiceShape service, OperationShape operation) {
        return operationPredicate.test(model, service, operation);
    }

    /**
     * Gets the config properties that will be added to the client config by this plugin.
     *
     * @return Returns the config properties to add to the client config.
     */
    public List<ConfigProperty> getConfigProperties() {
        return configProperties;
    }

    /**
     * @return Returns an optional reference to a callable that modifies client config.
     */
    public Optional<SymbolReference> getPythonPlugin() {
        return Optional.ofNullable(pythonPlugin);
    }

    /**
     * @return Returns an optional auth scheme to register.
     */
    public Optional<AuthScheme> getAuthScheme() {
        return Optional.ofNullable(authScheme);
    }

    /**
     * @return Returns a new builder for a {@link RuntimeClientPlugin}.
     */
    public static Builder builder() {
        return new Builder();
    }

    @Override
    public SmithyBuilder<RuntimeClientPlugin> toBuilder() {
        var builder = builder()
            .pythonPlugin(pythonPlugin)
            .authScheme(authScheme)
            .configProperties(configProperties);

        if (operationPredicate == OPERATION_ALWAYS_FALSE) {
            builder.servicePredicate(servicePredicate);
        } else {
            builder.operationPredicate(operationPredicate);
        }

        return builder;
    }

    /**
     * Builds a {@link RuntimeClientPlugin}.
     */
    public static final class Builder implements SmithyBuilder<RuntimeClientPlugin> {
        private BiPredicate<Model, ServiceShape> servicePredicate = (model, service) -> true;
        private OperationPredicate operationPredicate = OPERATION_ALWAYS_FALSE;
        private List<ConfigProperty> configProperties = new ArrayList<>();
        private SymbolReference pythonPlugin = null;
        private AuthScheme authScheme = null;

        Builder() {
        }

        @Override
        public RuntimeClientPlugin build() {
            return new RuntimeClientPlugin(this);
        }

        /**
         * Sets a predicate that determines if the plugin applies to a
         * specific operation.
         *
         * <p>When this method is called, the {@code servicePredicate} is
         * automatically configured to return false for every service.
         *
         * <p>By default, a plugin applies globally to a service, which thereby
         * applies to every operation when the interceptors list is copied.
         *
         * @param operationPredicate Operation matching predicate.
         * @return Returns the builder.
         * @see #servicePredicate(BiPredicate)
         */
        public Builder operationPredicate(OperationPredicate operationPredicate) {
            this.operationPredicate = Objects.requireNonNull(operationPredicate);
            servicePredicate = (model, service) -> false;
            return this;
        }

        /**
         * Configures a predicate that makes a plugin only apply to a set of
         * operations that match one or more of the set of given shape names,
         * and ensures that the plugin is not applied globally to services.
         *
         * <p>By default, a plugin applies globally to a service, which thereby
         * applies to every operation when the interceptors list is copied.
         *
         * @param operationNames Set of operation names.
         * @return Returns the builder.
         */
        public Builder appliesOnlyToOperations(Set<String> operationNames) {
            operationPredicate((model, service, operation) -> operationNames.contains(operation.getId().getName()));
            return servicePredicate((model, service) -> false);
        }

        /**
         * Configures a predicate that applies the plugin to a service if the
         * predicate matches a given model and service.
         *
         * <p>When this method is called, the {@code operationPredicate} is
         * automatically configured to return false for every operation,
         * causing the plugin to only apply to services and not to individual
         * operations.
         *
         * <p>By default, a plugin applies globally to a service, which
         * thereby applies to every operation when the interceptors list is
         * copied. Setting a custom service predicate is useful for plugins
         * that should only be applied to specific services or only applied
         * at the operation level.
         *
         * @param servicePredicate Service predicate.
         * @return Returns the builder.
         */
        public Builder servicePredicate(BiPredicate<Model, ServiceShape> servicePredicate) {
            this.servicePredicate = Objects.requireNonNull(servicePredicate);
            operationPredicate = OPERATION_ALWAYS_FALSE;
            return this;
        }

        /**
         * Sets the list of config properties to add to the client's config object.
         *
         * @param configProperties The list of config properties to add to the client's config object.
         * @return Returns the builder.
         */
        public Builder configProperties(List<ConfigProperty> configProperties) {
            this.configProperties = configProperties;
            return this;
        }

        /**
         * Adds a single config property which will be added to the client's config object.
         *
         * @param configProperty A config property to add to the client's config object.
         * @return Returns the builder.
         */
        public Builder addConfigProperty(ConfigProperty configProperty) {
            this.configProperties.add(configProperty);
            return this;
        }

        /**
         * Configures a python plugin to automatically add to the service or operation.
         *
         * @param pythonPlugin A reference to a callable that modifies the client config.
         * @return Returns the builder.
         */
        public Builder pythonPlugin(SymbolReference pythonPlugin) {
            this.pythonPlugin = pythonPlugin;
            return this;
        }

        /**
         * Configures an auth scheme which will be added to the client's supported
         * auth schemes.
         *
         * @param authScheme The auth scheme to register.
         * @return Returns the builder.
         */
        public Builder authScheme(AuthScheme authScheme) {
            this.authScheme = authScheme;
            return this;
        }
    }
}
