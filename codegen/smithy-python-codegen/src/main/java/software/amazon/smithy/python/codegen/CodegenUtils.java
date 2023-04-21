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

import static java.lang.String.format;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoField;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.utils.SetUtils;
import software.amazon.smithy.utils.StringUtils;

/**
 * Utility methods likely to be needed across packages.
 */
public final class CodegenUtils {

    /**
     * The maximum preferred line length for generated code. In most cases it won't
     * be practical to try to adhere to this in the generator, but we can make some
     * amount of effort. Eventually a formatter like black will be run on the output
     * to fix any lingering issues.
     */
    public static final int MAX_PREFERRED_LINE_LENGTH = 88;

    static final Set<String> ERROR_MESSAGE_MEMBER_NAMES = SetUtils.of(
            "errormessage", "error_message", "message");

    private static final Logger LOGGER = Logger.getLogger(CodegenUtils.class.getName());

    private CodegenUtils() {}

    /**
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the client's configuration object symbol.
     */
    public static Symbol getConfigSymbol(PythonSettings settings) {
        return Symbol.builder()
                .name("Config")
                .namespace(format("%s.config", settings.getModuleName()), ".")
                .definitionFile(format("./%s/config.py", settings.getModuleName()))
                .build();
    }

    /**
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the client's plugin type hint symbol.
     */
    public static Symbol getPluginSymbol(PythonSettings settings) {
        return Symbol.builder()
                .name("Plugin")
                .namespace(format("%s.config", settings.getModuleName()), ".")
                .definitionFile(format("./%s/config.py", settings.getModuleName()))
                .build();
    }

    /**
     * Gets the service error symbol.
     *
     * <p>This error is the top-level error for the client. Every error surfaced by
     * the client MUST be a subclass of this so that customers can reliably catch all
     * exceptions it raises. The client implementation will wrap any errors that aren't
     * already subclasses.
     *
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the symbol for the client's error class.
     */
    public static Symbol getServiceError(PythonSettings settings) {
        return Symbol.builder()
                .name("ServiceError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

    /**
     * Gets the service API error symbol.
     *
     * <p>This error is the parent class for all errors returned over the wire by the
     * service, including unknown errors.
     *
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the symbol for the client's API error class.
     */
    public static Symbol getApiError(PythonSettings settings) {
        return Symbol.builder()
                .name("ApiError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

    /**
     * Gets the unknown API error symbol.
     *
     * <p> This error is the parent class for all errors returned over the wire by
     * the service which aren't in the model.
     *
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the symbol for unknown API errors.
     */
    public static Symbol getUnknownApiError(PythonSettings settings) {
        return Symbol.builder()
                .name("UnknownApiError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

    /**
     * Gets the symbol for the http auth parameters object.
     *
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the symbol for http auth params.
     */
    public static Symbol getHttpAuthParamsSymbol(PythonSettings settings) {
        return Symbol.builder()
            .name("HTTPAuthParams")
            .namespace(format("%s.auth", settings.getModuleName()), ".")
            .definitionFile(format("./%s/auth.py", settings.getModuleName()))
            .build();
    }

    /**
     * Gets the symbol for the http auth scheme resolver.
     *
     * @param settings The client settings, used to account for module configuration.
     * @return Returns the http auth scheme resolver symbol.
     */
    public static Symbol getHttpAuthSchemeResolverSymbol(PythonSettings settings) {
        return Symbol.builder()
            .name("HTTPAuthSchemeResolver")
            .namespace(format("%s.auth", settings.getModuleName()), ".")
            .definitionFile(format("./%s/auth.py", settings.getModuleName()))
            .build();
    }

    /**
     * Determines whether a given member is probably the main "message" of an error shape.
     *
     * @param model The whole service model.
     * @param shape The member to check.
     * @return Returns whether the member is probably the error message.
     */
    static boolean isErrorMessage(Model model, MemberShape shape) {
        return ERROR_MESSAGE_MEMBER_NAMES.contains(shape.getMemberName().toLowerCase(Locale.US))
                && model.expectShape(shape.getContainer()).hasTrait(ErrorTrait.class);
    }

    /**
     * Executes a given shell command in a given directory.
     *
     * @param command The string command to execute, e.g. "python fmt".
     * @param directory The directory to run the command in.
     * @return Returns the console output of the command.
     */
    public static String runCommand(String command, Path directory) {
        String[] finalizedCommand;
        if (System.getProperty("os.name").toLowerCase().startsWith("windows")) {
            finalizedCommand = new String[]{"cmd.exe", "/c", command};
        } else {
            finalizedCommand = new String[]{"sh", "-c", command};
        }

        ProcessBuilder processBuilder = new ProcessBuilder(finalizedCommand)
                .redirectErrorStream(true)
                .directory(directory.toFile());

        try {
            Process process = processBuilder.start();
            List<String> output = new ArrayList<>();

            // Capture output for reporting.
            try (BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(
                    process.getInputStream(), Charset.defaultCharset()))) {
                String line;
                while ((line = bufferedReader.readLine()) != null) {
                    LOGGER.finest(line);
                    output.add(line);
                }
            }

            process.waitFor();
            process.destroy();

            String joinedOutput = String.join(System.lineSeparator(), output);
            if (process.exitValue() != 0) {
                throw new CodegenException(format(
                        "Command `%s` failed with output:%n%n%s", command, joinedOutput));
            }
            return joinedOutput;
        } catch (InterruptedException | IOException e) {
            throw new CodegenException(e);
        }
    }

    /**
     * Gets the name under which the given package will be exported by default.
     *
     * @param packageName The full package name of the exported package.
     * @return The name a the package will be imported under by default.
     */
    public static String getDefaultPackageImportName(String packageName) {
        if (StringUtils.isBlank(packageName) || !packageName.contains("/")) {
            return packageName;
        }
        return packageName.substring(packageName.lastIndexOf('/') + 1);
    }

    /**
     * Convert a map of k,v to a list of pairwise arrays.
     *
     * <p>For example:
     *
     * <pre>{@code
     * Map.of("a", 1, "b", 2) -> List.of({"a", 1}, {"b", 2})
     * }</pre>
     *
     * @param map The map to be converted
     * @return The list of arrays
     */
    public static List<Object[]> toTuples(Map<?, ?> map) {
        return map.entrySet().stream().map((entry) ->
                List.of(entry.getKey(), entry.getValue()).toArray()).toList();
    }

    /**
     * Generates a Python datetime constructor for the given ZonedDateTime.
     *
     * @param writer A writer to add dependencies to.
     * @param value The ZonedDateTime to convert.
     * @return A string containing a Python datetime constructor representing the given ZonedDateTime.
     */
    public static String getDatetimeConstructor(PythonWriter writer, ZonedDateTime value) {
        writer.addStdlibImport("datetime", "datetime");
        writer.addStdlibImport("datetime", "timezone");
        var timezone = "timezone.utc";
        if (value.getOffset() != ZoneOffset.UTC) {
            writer.addStdlibImport("datetime", "timedelta");
            timezone = String.format("timezone(timedelta(seconds=%d))", value.getOffset().getTotalSeconds());
        }
        return String.format("datetime(%d, %d, %d, %d, %d, %d, %d, %s)", value.get(ChronoField.YEAR),
            value.get(ChronoField.MONTH_OF_YEAR), value.get(ChronoField.DAY_OF_MONTH),
            value.get(ChronoField.HOUR_OF_DAY), value.get(ChronoField.MINUTE_OF_HOUR),
            value.get(ChronoField.SECOND_OF_MINUTE), value.get(ChronoField.MICRO_OF_SECOND), timezone);
    }

    /**
     * Parses a timestamp Node.
     *
     * <p>This is used to offload modeled timestamp parsing from Python runtime to Java build time.
     *
     * @param model The model being generated.
     * @param shape The shape of the node.
     * @param value The node to parse.
     * @return A parsed ZonedDateTime representation of the given node.
     */
    public static ZonedDateTime parseTimestampNode(Model model, Shape shape, Node value) {
        if (value.isNumberNode()) {
            return parseEpochTime(value);
        }

        Optional<TimestampFormatTrait> trait = shape.getTrait(TimestampFormatTrait.class);
        if (shape.isMemberShape()) {
            trait = shape.asMemberShape().get().getMemberTrait(model, TimestampFormatTrait.class);
        }
        var format = Format.DATE_TIME;
        if (trait.isPresent()) {
            format = trait.get().getFormat();
        }

        return switch (format) {
            case DATE_TIME -> parseDateTime(value);
            case HTTP_DATE -> parseHttpDate(value);
            default -> throw new CodegenException("Unexpected timestamp format: " + format);
        };
    }

    private static ZonedDateTime parseEpochTime(Node value) {
        Number number = value.expectNumberNode().getValue();
        Instant instant = Instant.ofEpochMilli(Double.valueOf(number.doubleValue() * 1000).longValue());
        return instant.atZone(ZoneId.of("UTC"));
    }

    private static ZonedDateTime parseDateTime(Node value) {
        Instant instant =  Instant.from(DateTimeFormatter.ISO_INSTANT.parse(value.expectStringNode().getValue()));
        return instant.atZone(ZoneId.of("UTC"));
    }

    private static ZonedDateTime parseHttpDate(Node value) {
        Instant instant = Instant.from(DateTimeFormatter.RFC_1123_DATE_TIME.parse(value.expectStringNode().getValue()));
        return instant.atZone(ZoneId.of("UTC"));
    }

    /**
     * Writes an accessor for a structure member, handling defaultedness and nullability.
     *
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param variableName The python variable name pointing to the structure to be accessed.
     * @param member The member to access.
     * @param runnable A runnable which uses the member.
     */
    public static void accessStructureMember(
        GenerationContext context,
        PythonWriter writer,
        String variableName,
        MemberShape member,
        Runnable runnable
    ) {
        accessStructureMember(context, writer, variableName, member, true, runnable);
    }

    /**
     * Writes an accessor for a structure member, handling defaultedness and nullability.
     *
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param variableName The python variable name pointing to the structure to be accessed.
     * @param member The member to access.
     * @param accessFalsey Whether to access falsey members such as empty strings.
     * @param runnable A runnable which uses the member.
     */
    public static void accessStructureMember(
        GenerationContext context,
        PythonWriter writer,
        String variableName,
        MemberShape member,
        boolean accessFalsey,
        Runnable runnable
    ) {
        var shouldDedent = false;
        var isNullable = NullableIndex.of(context.model()).isMemberNullable(member);
        var memberName = context.symbolProvider().toMemberName(member);
        if (!accessFalsey) {
            writer.write("if $L.$L:", variableName, memberName);
            writer.indent();
            shouldDedent = true;
        } else if (isNullable) {
            writer.write("if $L.$L is not None:", variableName, memberName);
            writer.indent();
            shouldDedent = true;
        }

        runnable.run();

        if (shouldDedent) {
            writer.dedent();
        }
    }
}
