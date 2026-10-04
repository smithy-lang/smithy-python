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
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Represents a property to be added to the generated client config object.
 *
 * <p>A property is a field on the config that participates in the resolution
 * pipeline. Its value comes, in priority order, from an explicit override, an
 * optional resolver, or a default. The emitters below write the body of the
 * corresponding {@code FieldSpec} entry; absent emitters mean a plain
 * {@code default=None} field.
 */
@SmithyUnstableApi
public final class ConfigProperty implements ToSmithyBuilder<ConfigProperty> {
    private final String name;
    private final Symbol type;
    private final Symbol inputType;
    private final boolean nullable;
    private final String documentation;
    private final Consumer<PythonWriter> defaultFactory;
    private final Consumer<PythonWriter> asyncDefaultFactory;
    private final Consumer<PythonWriter> converter;

    private ConfigProperty(Builder builder) {
        this.name = Objects.requireNonNull(builder.name);
        this.type = Objects.requireNonNull(builder.type);
        this.inputType = builder.inputType != null ? builder.inputType : this.type;
        this.nullable = builder.nullable;
        this.documentation = Objects.requireNonNull(builder.documentation);
        this.defaultFactory = builder.defaultFactory;
        this.asyncDefaultFactory = builder.asyncDefaultFactory;
        this.converter = builder.converter;
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
     * @return Returns the type accepted as an override for this field.
     *
     * <p>Defaults to {@link #type()}. Differs when the override type is not the same
     * as what finalizes on the config.
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
     * @return The emitter for the field's default_factory body, if any.
     *
     * <p>Writes the expression a zero-arg lambda returns, e.g. {@code AIOHTTPClient()}.
     * Absent means the field defaults to {@code None}.
     */
    public Optional<Consumer<PythonWriter>> defaultFactory() {
        return Optional.ofNullable(defaultFactory);
    }

    /**
     * @return The emitter for the field's async_default_factory body, if any.
     *
     * <p>Set when the async default is loop-bound (e.g. an aiohttp transport) and the
     * sync resolve path needs a blocking counterpart.
     */
    public Optional<Consumer<PythonWriter>> asyncDefaultFactory() {
        return Optional.ofNullable(asyncDefaultFactory);
    }

    /**
     * @return The emitter for the field's converter body, if any.
     *
     * <p>Writes a one-arg lambda applied to an override before it is set.
     */
    public Optional<Consumer<PythonWriter>> converter() {
        return Optional.ofNullable(converter);
    }

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
                .defaultFactory(defaultFactory)
                .asyncDefaultFactory(asyncDefaultFactory)
                .converter(converter);
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
        private Consumer<PythonWriter> defaultFactory;
        private Consumer<PythonWriter> asyncDefaultFactory;
        private Consumer<PythonWriter> converter;

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
         * Optionally differentiate the override type of a config property from its resolved type.
         *
         * @param inputType The type accepted as an override.
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
         * Sets the emitter for the field's default_factory body.
         *
         * <p>Writes the expression a zero-arg lambda returns. Omit for a field
         * that defaults to {@code None}.
         *
         * @param defaultFactory Writes the default_factory lambda body.
         * @return Returns the builder.
         */
        public Builder defaultFactory(Consumer<PythonWriter> defaultFactory) {
            this.defaultFactory = defaultFactory;
            return this;
        }

        /**
         * Sets the emitter for the field's async_default_factory body.
         *
         * @param asyncDefaultFactory Writes the async_default_factory lambda body.
         * @return Returns the builder.
         */
        public Builder asyncDefaultFactory(Consumer<PythonWriter> asyncDefaultFactory) {
            this.asyncDefaultFactory = asyncDefaultFactory;
            return this;
        }

        /**
         * Sets the emitter for the field's converter body.
         *
         * @param converter Writes the converter lambda body.
         * @return Returns the builder.
         */
        public Builder converter(Consumer<PythonWriter> converter) {
            this.converter = converter;
            return this;
        }
    }
}
