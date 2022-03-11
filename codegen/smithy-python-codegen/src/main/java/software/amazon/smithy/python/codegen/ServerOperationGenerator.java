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

package software.amazon.smithy.python.codegen;

import java.util.Iterator;
import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.OperationShape;

/**
 * Generates code for individual SSDK operations.
 */
final class ServerOperationGenerator implements Runnable {

    private static final String HAS_TYPE_VARS = "hasOperationTypeVars";
    private static final Logger LOGGER = Logger.getLogger(ServerSymbolVisitor.class.getName());

    private final Model model;
    private final OperationShape operation;
    private final PythonWriter writer;
    private final SymbolProvider symbolProvider;

    ServerOperationGenerator(
            Model model,
            OperationShape operation,
            PythonWriter writer,
            SymbolProvider symbolProvider
    ) {
        this.model = model;
        this.operation = operation;
        this.writer = writer;
        this.symbolProvider = symbolProvider;
    }

    @Override
    public void run() {
        writer.addStdlibImport("typing", "Protocol");

        Symbol operationSymbol = symbolProvider.toSymbol(operation);
        Symbol inputSymbol = symbolProvider.toSymbol(model.expectShape(operation.getInputShape()));
        Symbol outputSymbol = symbolProvider.toSymbol(model.expectShape(operation.getOutputShape()));

        writeTypeVars();

        writer.write("""
                class $1LWithContext(Protocol[K]):
                    async def __call__(self, request: $2T, context: K) -> $3T:
                        ...

                class $1LWithoutContext(Protocol):
                    async def __call__(self, request: $2T) -> $3T:
                        ...

                $1L = $1LWithContext[K] | $1LWithoutContext


                """, operationSymbol.getName(), inputSymbol, outputSymbol);

        Symbol errorsTypeSymbol = operationSymbol.expectProperty("errors", Symbol.class);

        if (operation.getErrors().isEmpty()) {
            writer.write("$L = None", errorsTypeSymbol.getName());
        } else {
            List<Symbol> errorSymbols = operation.getErrors().stream()
                    .map(model::expectShape)
                    .map(symbolProvider::toSymbol)
                    .toList();

            writer.writeInline("$L = ", errorsTypeSymbol.getName());
            for (Iterator<Symbol> i = errorSymbols.iterator(); i.hasNext();) {
                writer.writeInline("$T", i.next());
                if (i.hasNext()) {
                    writer.writeInline(" | ");
                }
            }
            writer.write("").write("");
        }

        // TODO: Use protocol IO symbols
        writer.addStdlibImport("typing", "Any");
        writer.addStdlibImport("typing", "Generic");
        Symbol serializerSymbol = operationSymbol.expectProperty("serializer", Symbol.class);
        writer.write("""
                class $1L(Generic[T]):
                    def serialize(self, obj: $2T, context: T | None = None) -> Any:
                        pass

                    def serialize_errors(self, e: Exception, context: T | None = None) -> Any:
                        pass

                    def deserialize(self, request: Any, context: T | None = None) -> $3T:
                        pass

                """, serializerSymbol.getName(), outputSymbol, inputSymbol);
    }

    // only writes out the type vars if the file doesn't already have them
    private void writeTypeVars() {
        if (Optional.ofNullable(writer.getContext(HAS_TYPE_VARS, Boolean.class)).orElse(false)) {
            return;
        }
        writer.addStdlibImport("typing", "TypeVar");

        writer.write("""
                # Generic TypeVar for any purpose
                T = TypeVar("T")

                # Used as a contravariant TypeVar for operation types
                K = TypeVar("K", contravariant=True)
                """);

        // Write context into the parent state
        writer.popState();
        writer.putContext(HAS_TYPE_VARS, true);
        writer.pushState();
    }
}
