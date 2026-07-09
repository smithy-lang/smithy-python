/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.utils.StringUtils;

public final class AwsServiceIdIntegration implements PythonIntegration {

    /**
     * SDK IDs of the AWS clients that were published under the unprefixed
     * {@code <SdkId>Client} name before the {@code Async} prefix was adopted.
     *
     * <p>Only these clients generate a deprecated alias for the old name so that
     * existing imports keep working. New clients are generated with the
     * {@code Async}-prefixed name from the start and need no alias. This set can
     * be removed once the aliases are dropped.
     */
    private static final Set<String> LEGACY_ALIAS_SDK_IDS = Set.of(
            "Bedrock Runtime",
            "ConnectHealth",
            "Lex Runtime V2",
            "Polly",
            "QBusiness",
            "SageMaker Runtime HTTP2",
            "Transcribe Streaming");

    @Override
    public SymbolProvider decorateSymbolProvider(Model model, PythonSettings settings, SymbolProvider symbolProvider) {
        return new ServiceIdSymbolProvider(symbolProvider);
    }

    private static class ServiceIdSymbolProvider implements SymbolProvider {

        private final SymbolProvider delegate;

        ServiceIdSymbolProvider(SymbolProvider delegate) {
            this.delegate = delegate;
        }

        @Override
        public Symbol toSymbol(Shape shape) {
            Symbol symbol = this.delegate.toSymbol(shape);
            if (shape.isServiceShape() && shape.hasTrait(ServiceTrait.class)) {
                var serviceTrait = shape.expectTrait(ServiceTrait.class);
                var baseClientName = StringUtils.capitalize(serviceTrait.getSdkId() + "Client").replace(" ", "");
                var symbolBuilder = symbol.toBuilder().name("Async" + baseClientName);
                // Only clients that already shipped under the unprefixed name get a
                // backwards-compatible alias; new clients start life Async-prefixed.
                if (LEGACY_ALIAS_SDK_IDS.contains(serviceTrait.getSdkId())) {
                    symbolBuilder.putProperty(SymbolProperties.DEPRECATED_ALIAS, baseClientName);
                }
                symbol = symbolBuilder.build();
            }
            return symbol;
        }

        @Override
        public String toMemberName(MemberShape shape) {
            return this.delegate.toMemberName(shape);
        }
    }
}
