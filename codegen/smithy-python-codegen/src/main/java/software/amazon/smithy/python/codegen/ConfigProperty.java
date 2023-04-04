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

package software.amazon.smithy.python.codegen;

import java.util.Objects;
import java.util.function.Consumer;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Represents a property to be added to the generated client config object.
 */
@SmithyUnstableApi
public final class ConfigProperty implements ToSmithyBuilder<ConfigProperty> {
    private final String name;
    private final Symbol type;
    private final boolean nullable;
    private final String documentation;
    private final Consumer<PythonWriter> initialize;

    /**
     * Constructor.
     */
    private ConfigProperty(Builder builder) {
        this.name = Objects.requireNonNull(builder.name);
        this.type = Objects.requireNonNull(builder.type);
        this.nullable = builder.nullable;
        this.documentation = Objects.requireNonNull(builder.documentation);
        this.initialize = Objects.requireNonNull(builder.initialize);
    }

    /**
     * @return Returns the name of the config field.
     */
    public String name() {
        return name;
    }

    /**
     * @return Returns the symbol representing the type of the config field.
     */
    public Symbol type() {
        return type;
    }

    /**
     * @return Returns whether the property is nullable.
     */
    public boolean isNullable() {
        return nullable;
    }

    /**
     * @return Returns the config field's documentation.
     */
    public String documentation() {
        return documentation;
    }

    /**
     * Initializes the config field on the config object.
     *
     * <p>This will be wrapped in an {@link InitializeConfigPropertySection}.
     *
     * @param writer The writer to write to.
     */
    public void initialize(PythonWriter writer) {
        writer.pushState(new InitializeConfigPropertySection(this));
        initialize.accept(writer);
        writer.popState();
    }

    /**
     * The section that handles initializing a config property inside __init__.
     *
     * @param property The property being initialized.
     */
    public record InitializeConfigPropertySection(ConfigProperty property) implements CodeSection {}

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public SmithyBuilder<ConfigProperty> toBuilder() {
        return builder()
            .name(name)
            .type(type)
            .nullable(nullable)
            .documentation(documentation)
            .initialize(initialize);
    }

    /**
     * Builds a {@link ConfigProperty}.
     */
    public static final class Builder implements SmithyBuilder<ConfigProperty> {
        private String name;
        private Symbol type;
        private boolean nullable = true;
        private String documentation;
        private Consumer<PythonWriter> initialize = writer -> writer.write("self.$1L = $1L", name);

        @Override
        public ConfigProperty build() {
            return new ConfigProperty(this);
        }

        /**
         * Sets the name of the config property.
         *
         * @param name The name to use for the config property.
         * @return Returns the builder.
         */
        public Builder name(String name) {
            this.name = name;
            return this;
        }

        /**
         * Sets the type to use for the config property.
         *
         * <p>Properties that are nullable must not have that reflected here.
         * Rather, the nullable builder property should be set. The config
         * generator will handle adjusting the type hints.
         *
         * @param type The type of the config property.
         * @return Returns the builder.
         */
        public Builder type(Symbol type) {
            this.type = type;
            return this;
        }

        /**
         * Sets whether the config property is nullable.
         *
         * <p>Defaults to true.
         *
         * <p>All properties will be optional on the config object's constructor,
         * regardless of whether this value is true or false. Properties that
         * are not nullable MUST set a default value in the initialize function.
         *
         * @param nullable Whether the property is nullable.
         * @return Returns the builder.
         */
        public Builder nullable(boolean nullable) {
            this.nullable = nullable;
            return this;
        }

        /**
         * Sets the documentation for the config property.
         *
         * @param documentation The documentation for the config property.
         * @return Returns the builder.
         */
        public Builder documentation(String documentation) {
            this.documentation = documentation;
            return this;
        }

        /**
         * Sets the initializer function for the config property.
         *
         * <p>This will be called when creating the __init__ function for the
         * client's Config object. It MUST set the property on "self" based
         * on the optional __init__ parameter of the same name.
         *
         * <p>By default, this directly sets whatever value was provided.
         *
         * @param initialize The initializer function for the property.
         * @return Returns the builder.
         */
        public Builder initialize(Consumer<PythonWriter> initialize) {
            this.initialize = initialize;
            return this;
        }
    }
}
