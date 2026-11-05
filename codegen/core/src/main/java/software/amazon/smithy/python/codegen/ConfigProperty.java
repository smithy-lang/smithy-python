/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.Objects;
import java.util.Optional;
import java.util.function.Consumer;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
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
    private final Symbol inputType;
    private final boolean nullable;
    private final String documentation;
    private final Consumer<PythonWriter> initialize;
    private final String endpointParameter;
    private final Consumer<PythonWriter> resolver;
    private final Consumer<PythonWriter> definitions;
    private final Symbol validator;

    /**
     * Constructor.
     */
    private ConfigProperty(Builder builder) {
        this.name = Objects.requireNonNull(builder.name);
        this.type = Objects.requireNonNull(builder.type);
        this.inputType = builder.inputType != null ? builder.inputType : this.type;
        this.nullable = builder.nullable;
        this.documentation = Objects.requireNonNull(builder.documentation);
        this.initialize = Objects.requireNonNull(builder.initialize);
        this.endpointParameter = builder.endpointParameter;
        this.resolver = builder.resolver;
        this.definitions = builder.definitions;
        this.validator = builder.validator;
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
     * @return Returns the type accepted by the __init__ parameter.
     *
     * <p>Defaults to {@link #type()}. Differs when the input type is not the same as
     * what finalizes on the config.
     */
    public Symbol inputType() {
        return inputType;
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
     * @return Returns the client context parameter whose value the field holds, if any.
     *
     * <p>A field that names a parameter replaces the field code generation would add for
     * it, and the endpoint rules read the parameter from this field.
     */
    public Optional<String> endpointParameter() {
        return Optional.ofNullable(endpointParameter);
    }

    /**
     * @return Returns the writer of the expression that resolves the field from the
     * environment and the shared config file, if any.
     */
    public Optional<Consumer<PythonWriter>> resolver() {
        return Optional.ofNullable(resolver);
    }

    /**
     * @return Returns the writer of the module-level code the field's resolver needs, such
     * as a function it names, if any. Configs write it above the config class.
     */
    public Optional<Consumer<PythonWriter>> definitions() {
        return Optional.ofNullable(definitions);
    }

    /**
     * @return Returns the function that validates the field's value, if any.
     */
    public Optional<Symbol> validator() {
        return Optional.ofNullable(validator);
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
                .inputType(inputType)
                .nullable(nullable)
                .documentation(documentation)
                .initialize(initialize)
                .endpointParameter(endpointParameter)
                .resolver(resolver)
                .definitions(definitions)
                .validator(validator);
    }

    /**
     * Builds a {@link ConfigProperty}.
     */
    public static final class Builder implements SmithyBuilder<ConfigProperty> {
        private String name;
        private Symbol type;
        private Symbol inputType;
        private boolean nullable = true;
        private String documentation;
        private Consumer<PythonWriter> initialize = writer -> writer.write("self.$1L = $1L", name);
        private String endpointParameter;
        private Consumer<PythonWriter> resolver;
        private Consumer<PythonWriter> definitions;
        private Symbol validator;

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
         * Optionally differentiate the input type of a config property from its resolved type.
         *
         * <p>Used when the input type is not the same as what finalizes on the config.
         *
         * @param inputType The type accepted by the __init__ parameter.
         * @return Returns the builder.
         */
        public Builder inputType(Symbol inputType) {
            this.inputType = inputType;
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

        /**
         * Sets the client context parameter whose value the field holds.
         *
         * <p>The field replaces the one code generation would add for the parameter, so it
         * can have another name, a resolver, or a validator.
         *
         * @param endpointParameter The client context parameter's name.
         * @return Returns the builder.
         */
        public Builder endpointParameter(String endpointParameter) {
            this.endpointParameter = endpointParameter;
            return this;
        }

        /**
         * Sets the writer of the expression that resolves the field from the environment
         * and the shared config file, such as a resolver function's name.
         *
         * <p>Only configs that resolve their fields that way use it.
         *
         * @param resolver Writes the resolver expression inline.
         * @return Returns the builder.
         */
        public Builder resolver(Consumer<PythonWriter> resolver) {
            this.resolver = resolver;
            return this;
        }

        /**
         * Sets the writer of the module-level code the field's resolver needs, such as a
         * function it names. Configs write it above the config class, since the class
         * refers to the resolver when it is created.
         *
         * @param definitions Writes the module-level code.
         * @return Returns the builder.
         */
        public Builder definitions(Consumer<PythonWriter> definitions) {
            this.definitions = definitions;
            return this;
        }

        /**
         * Sets the function that validates the field's value.
         *
         * <p>Only configs that resolve their fields from the environment use it.
         *
         * @param validator The validator function.
         * @return Returns the builder.
         */
        public Builder validator(Symbol validator) {
            this.validator = validator;
            return this;
        }
    }
}
