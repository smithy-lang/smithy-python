/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Manages writers for Python files.
 */
@SmithyInternalApi
public final class PythonDelegator extends WriterDelegator<PythonWriter> {

    public PythonDelegator(
            FileManifest fileManifest,
            SymbolProvider symbolProvider,
            PythonSettings settings
    ) {
        super(
                fileManifest,
                new EnumSymbolProviderWrapper(symbolProvider),
                new PythonWriter.PythonWriterFactory(settings));
    }

    private static final class EnumSymbolProviderWrapper implements SymbolProvider {

        private final SymbolProvider wrapped;

        EnumSymbolProviderWrapper(SymbolProvider wrapped) {
            this.wrapped = wrapped;
        }

        @Override
        public Symbol toSymbol(Shape shape) {
            Symbol symbol = wrapped.toSymbol(shape);
            if (shape.isEnumShape() || shape.isIntEnumShape()) {
                symbol = symbol.expectProperty(SymbolProperties.ENUM_SYMBOL);
            }
            return symbol;
        }

        @Override
        public String toMemberName(MemberShape shape) {
            return wrapped.toMemberName(shape);
        }
    }
}
