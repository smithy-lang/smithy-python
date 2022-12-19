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

package software.amazon.smithy.python.codegen.integration;

import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Utility methods for generating HTTP-based protocols.
 */
@SmithyUnstableApi
public final class HttpProtocolGeneratorUtils {

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
        switch (format) {
            case DATE_TIME:
                return result + ".isoformat()";
            case EPOCH_SECONDS:
                return "str(" + result + ".timestamp())";
            case HTTP_DATE:
                writer.addStdlibImport("email.utils", "format_datetime");
                return "format_datetime(" + result + ", usegmt=True)";
            default:
                throw new CodegenException("Unexpected timestamp format `" + format + "` on " + shape);
        }
    }
}
