/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class ServiceErrorGenerator implements Runnable {
    private final PythonSettings settings;
    private final WriterDelegator<PythonWriter> writers;

    public ServiceErrorGenerator(
            PythonSettings settings,
            WriterDelegator<PythonWriter> writers
    ) {
        this.settings = settings;
        this.writers = writers;
    }

    @Override
    public void run() {
        var serviceError = CodegenUtils.getServiceError(settings);
        writers.useFileWriter(serviceError.getDefinitionFile(), serviceError.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addImport("smithy_core.exceptions", "ModeledError");
            writer.write("""
                    class $L(ModeledError):
                        ""\"Base error for all errors in the service.

                        Some exceptions do not extend from this class, including
                        synthetic, implicit, and shared exception types.
                        ""\"
                    """, serviceError.getName());
        });
    }
}
