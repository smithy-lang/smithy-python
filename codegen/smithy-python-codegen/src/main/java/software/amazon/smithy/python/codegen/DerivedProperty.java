/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen;

import java.util.Objects;
import java.util.Optional;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * A property for some generated intermediate configuration.
 *
 * <p>This allows for automatically populating the intermediate config.
 */
public final class DerivedProperty implements ToSmithyBuilder<DerivedProperty> {
    private final String name;
    private final Source source;
    private final Symbol type;
    private final Symbol initializationFunction;
    private final String sourcePropertyName;

    private DerivedProperty(Builder builder) {
        this.name = Objects.requireNonNull(builder.name);
        this.source = Objects.requireNonNull(builder.source);
        this.type = Objects.requireNonNull(builder.type);
        this.initializationFunction = builder.initializationFunction;

        if (builder.sourcePropertyName == null && builder.initializationFunction == null) {
            this.sourcePropertyName = this.name;
        } else {
            this.sourcePropertyName = builder.sourcePropertyName;
        }
    }

    /**
     * @return Returns the name of the property on the intermediate config.
     */
    public String name() {
        return name;
    }

    /**
     * Gets the source where the property should be derived from.
     *
     * <p> If an {@code initializationFunction} is defined, the source will be passed
     * to it. Otherwise, the property will be extracted from it based on the
     * {@code sourceProperty}.
     *
     * @return Returns the source of the derived config property.
     */
    public Source source() {
        return source;
    }

    /**
     * @return Returns the symbol representing the property's type.
     */
    public Symbol type() {
        return type;
    }

    /**
     * Gets the optional function used to initialize the derived property.
     *
     * <p>This function will be given the {@code source}.
     *
     * <p>This is mutually exclusive with {@code sourcePropertyName}.
     *
     * @return Optionally returns the symbol for a property initialization function.
     */
    public Optional<Symbol> initializationFunction() {
        return Optional.ofNullable(initializationFunction);
    }

    /**
     * Gets the optional property name on the source that maps to this property.
     *
     * <p>If present, the derived property will be directly mapped to the named
     * source property.
     *
     * <p>This is mutually exclusive with {@code initializationFunction}.
     *
     * @return Returns the name of the property on the source.
     */
    public Optional<String> sourcePropertyName() {
        return Optional.ofNullable(sourcePropertyName);
    }

    @Override
    public SmithyBuilder<DerivedProperty> toBuilder() {
        var builder = builder()
            .name(name)
            .source(source);

        initializationFunction().ifPresent(builder::initializationFunction);
        sourcePropertyName().ifPresent(builder::sourcePropertyName);
        return builder;
    }

    /**
     * @return Returns a builder for a {@link DerivedProperty}.
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * The source that the derived property is derived from.
     */
    public enum Source {

        /**
         * Indicates that the property is derived from the service config object.
         */
        CONFIG {
            @Override
            public String scopeLocation() {
                return "config";
            }
        },

        /**
         * Indicates that the property is derived from the operation input.
         */
        INPUT {
            @Override
            public String scopeLocation() {
                return "context.input";
            }
        };

        /**
         * @return Returns the symbol in scope mapping to the location.
         */
        public abstract String scopeLocation();
    }

    /**
     * A builder for {@link DerivedProperty}.
     */
    public static final class Builder implements SmithyBuilder<DerivedProperty> {
        private String name;
        private Source source = Source.CONFIG;
        private Symbol type;
        private Symbol initializationFunction;
        private String sourcePropertyName;

        @Override
        public DerivedProperty build() {
            return new DerivedProperty(this);
        }

        /**
         * Sets the name of the property on the intermediate config.
         *
         * @param name The property's name.
         * @return Returns the builder.
         */
        public Builder name(String name) {
            this.name = name;
            return this;
        }

        /**
         * Sets the source where the property should be derived from.
         *
         * <p> If an {@code initializationFunction} is defined, the source will be passed
         * to it. Otherwise, the property will be extracted from it based on the
         * {@code sourceProperty}.
         *
         * @param source The property's source.
         * @return Returns the builder.
         */
        public Builder source(Source source) {
            this.source = source;
            return this;
        }

        /**
         * Sets the symbol representing the type of the derived property.
         *
         * @param type The property's type symbol.
         * @return Returns the builder.
         */
        public Builder type(Symbol type) {
            this.type = type;
            return this;
        }

        /**
         * Gets the optional function used to initialize the derived property.
         *
         * <p>This function will be given the {@code source}.
         *
         * <p>This is mutually exclusive with {@code sourcePropertyName}. If set,
         * any value for {@code sourcePropertyName} will be nullified.
         *
         * @param initializationFunction The property's initialization function.
         * @return Returns the builder.
         */
        public Builder initializationFunction(Symbol initializationFunction) {
            this.sourcePropertyName = null;
            this.initializationFunction = initializationFunction;
            return this;
        }

        /**
         * Sets the optional property name on the source that maps to this property.
         *
         * <p>If present, the derived property will be directly mapped to the named
         * source property.
         *
         * <p>This is mutually exclusive with {@code initializationFunction}. If set,
         * any value for {@code initializationFunction} will be nullified.
         *
         * <p>By default, this value will be set to the value of {@code name}.
         *
         * @param sourceProperty The property's source property.
         * @return Returns the builder.
         */
        public Builder sourcePropertyName(String sourceProperty) {
            this.initializationFunction = null;
            this.sourcePropertyName = sourceProperty;
            return this;
        }
    }
}
