/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import software.amazon.smithy.python.codegen.ConfigField;
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
    private final List<ConfigField> configFields;

    private RuntimeClientPlugin(Builder builder) {
        configFields = Collections.unmodifiableList(builder.configFields);
    }

    /**
     * Gets the config fields that will be added to the client config by this plugin.
     *
     * @return Returns the config fields to add to the client config.
     */
    public List<ConfigField> getConfigFields() {
        return configFields;
    }

    /**
     * @return Returns a new builder for a {@link RuntimeClientPlugin}.
     */
    public static Builder builder() {
        return new Builder();
    }

    @Override
    public SmithyBuilder<RuntimeClientPlugin> toBuilder() {
        return new Builder();
    }

    /**
     * Builds a {@link RuntimeClientPlugin}.
     */
    public static final class Builder implements SmithyBuilder<RuntimeClientPlugin> {
        private List<ConfigField> configFields = new ArrayList<>();

        Builder() {
        }

        @Override
        public RuntimeClientPlugin build() {
            return new RuntimeClientPlugin(this);
        }

        /**
         * Sets the list of config fields to add to the client's config object.
         *
         * @param configFields The list of config fields to add to the client's config object.
         * @return Returns the builder.
         */
        public Builder configFields(List<ConfigField> configFields) {
            this.configFields = configFields;
            return this;
        }

        /**
         * Adds a single config field which will be added to the client's config object.
         *
         * @param configField A config field to add to the client's config object.
         * @return Returns the builder.
         */
        public Builder addConfigField(ConfigField configField) {
            this.configFields.add(configField);
            return this;
        }
    }
}
