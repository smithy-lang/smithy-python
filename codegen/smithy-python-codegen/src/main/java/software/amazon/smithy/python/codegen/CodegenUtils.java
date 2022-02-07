/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.traits.ErrorTrait;
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
     * Detects if an annotated mediatype indicates JSON contents.
     *
     * @param mediaType The media type to inspect.
     * @return If the media type indicates JSON contents.
     */
    public static boolean isJsonMediaType(String mediaType) {
        return mediaType.equals("application/json") || mediaType.endsWith("+json");
    }

    static Symbol getDefaultTimestamp(PythonSettings settings) {
        return Symbol.builder()
                .name("DEFAULT_TIMESTAMP")
                .namespace(format("%s.utils", settings.getModuleName()), ".")
                .definitionFile(format("./%s/utils.py", settings.getModuleName()))
                .build();
    }

    static Symbol getServiceError(PythonSettings settings) {
        return Symbol.builder()
                .name("ServiceError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

    static Symbol getApiError(PythonSettings settings) {
        return Symbol.builder()
                .name("ApiError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

    static Symbol getUnknownApiError(PythonSettings settings) {
        return Symbol.builder()
                .name("UnknownApiError")
                .namespace(format("%s.errors", settings.getModuleName()), ".")
                .definitionFile(format("./%s/errors.py", settings.getModuleName()))
                .build();
    }

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
}
