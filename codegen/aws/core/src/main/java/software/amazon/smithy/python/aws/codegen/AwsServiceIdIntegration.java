/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.utils.StringUtils;

public final class AwsServiceIdIntegration implements PythonIntegration {
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
                var serviceName = StringUtils.capitalize(serviceTrait.getSdkId()).replace(" ", "");
                symbol = symbol.toBuilder().name(serviceName).build();
            }
            return symbol;
        }

        @Override
        public String toMemberName(MemberShape shape) {
            return this.delegate.toMemberName(shape);
        }
    }
}
