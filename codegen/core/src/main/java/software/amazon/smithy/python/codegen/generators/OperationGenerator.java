/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.List;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class OperationGenerator implements Runnable {
    private static final Logger LOGGER = Logger.getLogger(OperationGenerator.class.getName());

    private final GenerationContext context;
    private final PythonWriter writer;
    private final OperationShape shape;
    private final SymbolProvider symbolProvider;
    private final Model model;

    public OperationGenerator(GenerationContext context, PythonWriter writer, OperationShape shape) {
        this.context = context;
        this.writer = writer;
        this.shape = shape;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
    }

    @Override
    public void run() {
        var opSymbol = symbolProvider.toSymbol(shape);
        writer.addLocallyDefinedSymbol(opSymbol);
        var inSymbol = symbolProvider.toSymbol(model.expectShape(shape.getInputShape()));
        var outSymbol = symbolProvider.toSymbol(model.expectShape(shape.getOutputShape()));

        writer.addStdlibImport("dataclasses", "dataclass");
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

        writer.write("""
                $1L = $2T(
                        input = $3T,
                        output = $4T,
                        schema = $5T,
                        input_schema = $6T,
                        output_schema = $7T,
                        error_registry = $8T({
                            $9C
                        }),
                        effective_auth_schemes = [
                            ${10C}
                        ],
                        error_schemas = [
                            ${11C}
                        ]
                )
                """,
                opSymbol.getName(),
                RuntimeTypes.API_OPERATION,
                inSymbol,
                outSymbol,
                opSymbol.expectProperty(SymbolProperties.SCHEMA),
                inSymbol.expectProperty(SymbolProperties.SCHEMA),
                outSymbol.expectProperty(SymbolProperties.SCHEMA),
                RuntimeTypes.TYPE_REGISTRY,
                writer.consumer(this::writeErrorTypeRegistry),
                writer.consumer(this::writeAuthSchemes),
                writer.consumer(this::writeErrorSchemas));
    }

    private void writeErrorTypeRegistry(PythonWriter writer) {
        List<ShapeId> errors = shape.getErrors();
        for (var error : errors) {
            var errSymbol = symbolProvider.toSymbol(model.expectShape(error));
            writer.write("$1T($2S): $3T,", RuntimeTypes.SHAPE_ID, error, errSymbol);
        }
    }

    private void writeErrorSchemas(PythonWriter writer) {
        for (var error : shape.getErrors()) {
            var errSymbol = symbolProvider.toSymbol(model.expectShape(error));
            writer.write("$T,", errSymbol.expectProperty(SymbolProperties.SCHEMA));
        }
    }

    private void writeAuthSchemes(PythonWriter writer) {
        var authSchemes = ServiceIndex.of(model)
                .getEffectiveAuthSchemes(context.settings().service(),
                        shape.getId(),
                        ServiceIndex.AuthSchemeMode.NO_AUTH_AWARE);

        for (var authSchemeId : authSchemes.keySet()) {
            writer.write("$1T($2S),", RuntimeTypes.SHAPE_ID, authSchemeId);
        }

    }
}
