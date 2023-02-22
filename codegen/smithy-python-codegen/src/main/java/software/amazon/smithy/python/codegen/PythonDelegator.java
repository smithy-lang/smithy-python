/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;

/**
 * Manages writers for Python files.
 */
final class PythonDelegator extends WriterDelegator<PythonWriter> {

    PythonDelegator(
            FileManifest fileManifest,
            SymbolProvider symbolProvider,
            PythonSettings settings
    ) {
        super(
                fileManifest,
                new EnumSymbolProviderWrapper(symbolProvider),
                new PythonWriter.PythonWriterFactory(settings)
        );
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
                symbol = symbol.expectProperty("enumSymbol", Symbol.class);
            }
            return symbol;
        }

        @Override
        public String toMemberName(MemberShape shape) {
            return wrapped.toMemberName(shape);
        }
    }
}
