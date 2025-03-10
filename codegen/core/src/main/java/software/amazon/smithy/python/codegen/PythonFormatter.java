/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.logging.Logger;
import java.util.regex.Pattern;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.python.codegen.generators.SetupGenerator;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class PythonFormatter implements Runnable {
    private static final Logger LOGGER = Logger.getLogger(PythonFormatter.class.getName());
    private static final int PYTHON_MINOR_VERSION = 12; // 3.12

    private final GenerationContext context;

    public PythonFormatter(GenerationContext context) {
        this.context = context;
    }

    @Override
    public void run() {
        Pattern versionPattern = Pattern.compile("Python \\d\\.(?<minor>\\d+)\\.(?<patch>\\d+)");
        FileManifest fileManifest = context.fileManifest();
        SetupGenerator.generateSetup(context.settings(), context);

        LOGGER.info("Flushing writers in preparation for formatting and linting.");
        context.writerDelegator().flushWriters();

        String output;
        try {
            LOGGER.info("Attempting to discover python version");
            output = CodegenUtils.runCommand("python3 --version", fileManifest.getBaseDir()).strip();
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find python on the path. Skipping formatting and type checking.");
            return;
        }
        var matcher = versionPattern.matcher(output);
        if (!matcher.find()) {
            LOGGER.warning("Unable to parse python version string. Skipping formatting and type checking.");
        }
        int minorVersion = Integer.parseInt(matcher.group("minor"));
        if (minorVersion < PYTHON_MINOR_VERSION) {
            LOGGER.warning(String.format("""
                    Found incompatible python version 3.%s.%s, expected 3.12.0 or greater. \
                    Skipping formatting and type checking.""",
                    matcher.group("minor"),
                    matcher.group("patch")));
            return;
        }
        LOGGER.info("Verifying python files");
        for (var file : fileManifest.getFiles()) {
            var fileName = file.getFileName();
            if (fileName == null || !fileName.endsWith(".py")) {
                continue;
            }
            CodegenUtils.runCommand("python3 " + file, fileManifest.getBaseDir());
        }
        format(fileManifest);
        typeCheck(fileManifest);
    }

    private void format(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m ruff -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the python package ruff. Skipping formatting.");
            return;
        }
        LOGGER.info("Running code formatter on generated code");
        CodegenUtils.runCommand("python3 -m ruff format", fileManifest.getBaseDir());
    }

    private void typeCheck(FileManifest fileManifest) {
        try {
            CodegenUtils.runCommand("python3 -m pyright -h", fileManifest.getBaseDir());
        } catch (CodegenException e) {
            LOGGER.warning("Unable to find the pyright package. Skipping type checking.");
            return;
        }
        LOGGER.info("Running type checker on generated code");
        CodegenUtils.runCommand("python3 -m pyright .", fileManifest.getBaseDir());
    }
}
