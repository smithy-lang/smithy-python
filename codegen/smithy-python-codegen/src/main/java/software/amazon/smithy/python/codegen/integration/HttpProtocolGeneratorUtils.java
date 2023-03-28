/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

package software.amazon.smithy.python.codegen.integration;

import static java.lang.String.format;

import java.util.Locale;
import java.util.function.Function;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.selector.Selector;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.TriConsumer;

/**
 * Utility methods for generating HTTP-based protocols.
 */
@SmithyUnstableApi
public final class HttpProtocolGeneratorUtils {
    // Shape is an error on an operation shape that has the httpPayload trait applied to it
    // See: https://smithy.io/2.0/spec/selectors.html for more information on selectors
    private static final Selector PAYLOAD_ERROR_SELECTOR = Selector.parse(
        "operation -[error]-> structure :test(> member :test([trait|httpPayload]))"
    );

    private HttpProtocolGeneratorUtils() {
    }

    /**
     * Given a format and a source of data, generate an input value provider for the
     * timestamp.
     *
     * @param context The generation context.
     * @param writer The writer this param is being written to. Used only to add
     *               dependencies if necessary.
     * @param dataSource The in-code location of the data to provide an input of
     *                   ({@code input.foo}, {@code entry}, etc.)
     * @param shape The shape that represents the value being provided.
     * @param format The timestamp format to provide.
     * @return Returns a value or expression of the input timestamp.
     */
    public static String getTimestampInputParam(
        GenerationContext context,
        PythonWriter writer,
        String dataSource,
        Shape shape,
        Format format
    ) {
        writer.addImport("smithy_python.utils", "ensure_utc");
        var result = "ensure_utc(" + dataSource + ")";
        // see: https://smithy.io/2.0/spec/protocol-traits.html#smithy-api-timestampformat-trait
        switch (format) {
            case DATE_TIME:
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python.utils", "serialize_rfc3339");
                return String.format("serialize_rfc3339(%s)", result);
            case EPOCH_SECONDS:
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python.utils", "serialize_epoch_seconds");
                return String.format("serialize_epoch_seconds(%s)", result);
            case HTTP_DATE:
                writer.addStdlibImport("email.utils", "format_datetime");
                return "format_datetime(" + result + ", usegmt=True)";
            default:
                throw new CodegenException("Unexpected timestamp format `" + format + "` on " + shape);
        }
    }

    /**
     * Given a format and a source of data, generate an output value provider for the
     * timestamp.
     *
     * @param writer The current writer (so that imports may be added)
     * @param dataSource The in-code location of the data to provide an output of
     *                   ({@code output.foo}, {@code entry}, etc.)
     * @param shape The shape that represents the value being received.
     * @param format The timestamp format to provide.
     * @return Returns a value or expression of the output timestamp.
     */
    public static String getTimestampOutputParam(
        PythonWriter writer,
        String dataSource,
        Shape shape,
        Format format
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.utils", "expect_type");
        // see: https://smithy.io/2.0/spec/protocol-traits.html#smithy-api-timestampformat-trait
        switch (format) {
            case DATE_TIME -> {
                writer.addImport("smithy_python.utils", "ensure_utc");
                writer.addStdlibImport("datetime", "datetime");
                return format("ensure_utc(datetime.fromisoformat(expect_type(str, %s)))", dataSource);
            }
            case EPOCH_SECONDS -> {
                writer.addImport("smithy_python.utils", "epoch_seconds_to_datetime");
                return format("epoch_seconds_to_datetime(expect_type(int | float, %s))", dataSource);
            }
            case HTTP_DATE -> {
                writer.addImport("smithy_python.utils", "ensure_utc");
                writer.addStdlibImport("email.utils", "parsedate_to_datetime");
                return format("ensure_utc(parsedate_to_datetime(expect_type(str, %s)))", dataSource);
            }
            default -> throw new CodegenException("Unexpected timestamp format `" + format + "` on " + shape);
        }
    }

    /**
     * Generates a function that inspects error codes and dispatches to the proper deserialization function.
     *
     * @param context The generation context.
     * @param operation The operation to generate the dispatcher for.
     * @param errorShapeToCode A function that maps an error structure to it's code on the wire.
     * @param errorMessageCodeGenerator A consumer that generates code to extract the error message and code.
     *                                  It must set the code to the variable {@literal code}, the message to
     *                                  {@literal message}, and if it parses the body it must set the parsed
     *                                  body to {@literal parsed_body}.
     */
    public static void generateErrorDispatcher(
        GenerationContext context,
        OperationShape operation,
        Function<StructureShape, String> errorShapeToCode,
        TriConsumer<GenerationContext, PythonWriter, Boolean> errorMessageCodeGenerator
    ) {
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var transportResponse = context.applicationProtocol().responseType();
        var delegator = context.writerDelegator();
        var errorDispatcher = context.protocolGenerator().getErrorDeserializationFunction(context, operation);
        var apiError = CodegenUtils.getApiError(context.settings());
        var unknownApiError = CodegenUtils.getUnknownApiError(context.settings());
        var canReadResponseBody = canReadResponseBody(operation, context.model());
        delegator.useFileWriter(errorDispatcher.getDefinitionFile(), errorDispatcher.getNamespace(), writer -> {
            writer.pushState(new ErrorDispatcherSection(operation, errorShapeToCode, errorMessageCodeGenerator));
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                    async def $1L(http_response: $2T, config: $3T) -> $4T[Any]:
                        ${6C|}

                        match code.lower():
                            ${7C|}

                            case _:
                                return $5T(message)
                    """, errorDispatcher.getName(), transportResponse, configSymbol, apiError, unknownApiError,
                    writer.consumer(w -> errorMessageCodeGenerator.accept(context, w, canReadResponseBody)),
                    writer.consumer(w -> errorCases(context, w, operation, errorShapeToCode)));
            writer.popState();
        });
    }

    /**
     * Checks if the http_response.body can be read for a given operation shape.
     * <p>
     * If any of the errors for an operation contain an HttpPayload then it is not safe to read
     * the body of the http_response.
     *
     * @param operationShape operation shape to check
     * @param model smithy model
     */
    private static boolean canReadResponseBody(OperationShape operationShape, Model model) {
        return PAYLOAD_ERROR_SELECTOR.shapes(model)
            .map(Shape::getId)
            .noneMatch(shapeId -> operationShape.getErrors().contains(shapeId));
    }

    private static void errorCases(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        Function<StructureShape, String> errorShapeToCode
    ) {
        var errorIds = operation.getErrors(context.settings().getService(context.model()));
        for (ShapeId errorId : errorIds) {
            var error = context.model().expectShape(errorId, StructureShape.class);
            var code = errorShapeToCode.apply(error).toLowerCase(Locale.US);
            var deserFunction = context.protocolGenerator().getErrorDeserializationFunction(context, errorId);
            writer.write("""
                case $S:
                    return await $T(http_response, config, parsed_body, message)
                """, code, deserFunction);
        }
    }

    /**
     * Gets the output shape for an error or operation.
     * <p>
     * If the shape is an error, the error is returned, otherwise the operation output is returned.
     *
     * @param context Code generation context
     * @param operationOrError operation or error shape to find output shape for
     * @return output shape
     */
    public static Shape getOutputShape(GenerationContext context, Shape operationOrError) {
        var outputShape = operationOrError;
        if (operationOrError.isOperationShape()) {
            outputShape = context.model().expectShape(operationOrError.asOperationShape().get().getOutputShape());
        }
        return outputShape;
    }

    /**
     * A section that controls writing out the error dispatcher function.
     *
     * @param operation The operation whose deserializer is being generated.
     * @param errorShapeToCode A function that maps an error structure to it's code on the wire.
     * @param errorMessageCodeGenerator A consumer that generates code to extract the error message and code.
     */
    public record ErrorDispatcherSection(
        OperationShape operation,
        Function<StructureShape, String> errorShapeToCode,
        TriConsumer<GenerationContext, PythonWriter, Boolean> errorMessageCodeGenerator
    ) implements CodeSection {}
}
