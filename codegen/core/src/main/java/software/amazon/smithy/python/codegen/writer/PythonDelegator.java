/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.python.codegen.PythonSettings;
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
                symbolProvider,
                new PythonWriter.PythonWriterFactory(settings));
    }
}
