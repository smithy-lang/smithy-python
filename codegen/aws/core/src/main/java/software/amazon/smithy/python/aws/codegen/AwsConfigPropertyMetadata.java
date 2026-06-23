/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Optional;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * AWS-specific config resolution metadata for a config property.
 * Holds validators, custom resolvers, and default values.
 */
@SmithyInternalApi
public record AwsConfigPropertyMetadata(
        Symbol validator,
        Symbol customResolver,
        String defaultValue
) {
    public Optional<Symbol> validatorOpt() {
        return Optional.ofNullable(validator);
    }

    public Optional<Symbol> customResolverOpt() {
        return Optional.ofNullable(customResolver);
    }

    public Optional<String> defaultValueOpt() {
        return Optional.ofNullable(defaultValue);
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private Symbol validator;
        private Symbol customResolver;
        private String defaultValue;

        public Builder validator(Symbol validator) {
            this.validator = validator;
            return this;
        }

        public Builder customResolver(Symbol customResolver) {
            this.customResolver = customResolver;
            return this;
        }

        public Builder defaultValue(String defaultValue) {
            this.defaultValue = defaultValue;
            return this;
        }

        public AwsConfigPropertyMetadata build() {
            return new AwsConfigPropertyMetadata(validator, customResolver, defaultValue);
        }
    }
}
