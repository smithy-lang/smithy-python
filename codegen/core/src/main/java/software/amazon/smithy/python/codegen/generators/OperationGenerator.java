/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

import java.util.List;
import java.util.logging.Logger;

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
        var inSymbol = symbolProvider.toSymbol(model.expectShape(shape.getInputShape()));
        var outSymbol = symbolProvider.toSymbol(model.expectShape(shape.getOutputShape()));

        writer.addStdlibImport("dataclasses", "dataclass");
        writer.addImport("smithy_core.schemas", "APIOperation");
        writer.addImport("smithy_core.type_registry", "TypeRegistry");

        writer.write("""
                @dataclass(kw_only=True, frozen=True)
                class $1L(APIOperation["$2T", "$3T"]):
                        input = $2T                        
                        output = $3T
                        schema = $4T
                        input_schema = $5T
                        output_schema = $6T
                        error_registry = TypeRegistry({
                            $7C
                        })
                        effective_auth_schemes = [
                            $8C
                        ]
                """,
                opSymbol.getName(),
                inSymbol,
                outSymbol,
                opSymbol.expectProperty(SymbolProperties.SCHEMA),
                inSymbol.expectProperty(SymbolProperties.SCHEMA),
                outSymbol.expectProperty(SymbolProperties.SCHEMA),
                writer.consumer(this::writeErrorTypeRegistry),
                writer.consumer(this::writeAuthSchemes)
                // TODO: Docs? Maybe not necessary on the operation type itself
                // TODO: Singleton?
        );
    }

    private void writeErrorTypeRegistry(PythonWriter writer) {
        List<ShapeId> errors = shape.getErrors();
        if (!errors.isEmpty()) {
            writer.addImport("smithy_core.shapes", "ShapeID");
        }
        for (var error : errors) {
            var errSymbol = symbolProvider.toSymbol(model.expectShape(error));
            writer.write("ShapeID($S): $T,", error, errSymbol);
        }
    }

    private void writeAuthSchemes(PythonWriter writer) {
        var authSchemes = ServiceIndex.of(model).getEffectiveAuthSchemes(context.settings().service(), shape.getId(),
                ServiceIndex.AuthSchemeMode.NO_AUTH_AWARE);

        if (!authSchemes.isEmpty()) {
            writer.addImport("smithy_core.shapes", "ShapeID");
        }

        for(var authSchemeId : authSchemes.keySet()) {
            writer.write("ShapeID($S)", authSchemeId);
        }

    }
}
