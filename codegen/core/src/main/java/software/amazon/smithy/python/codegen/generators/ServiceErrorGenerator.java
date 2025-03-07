/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.Set;
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
            writer.addImport("smithy_core.exceptions", "SmithyException");
            writer.write("""
                    class $L(SmithyException):
                        ""\"Base error for all errors in the service.""\"
                        pass
                    """, serviceError.getName());
        });

        var apiError = CodegenUtils.getApiError(settings);
        writers.useFileWriter(apiError.getDefinitionFile(), apiError.getNamespace(), writer -> {
            writer.addStdlibImports("typing", Set.of("Literal", "ClassVar"));
            var unknownApiError = CodegenUtils.getUnknownApiError(settings);

            writer.write("""
                    @dataclass
                    class $1L($2T):
                        ""\"Base error for all API errors in the service.""\"
                        code: ClassVar[str]
                        fault: ClassVar[Literal["client", "server"]]

                        message: str

                        def __post_init__(self) -> None:
                            super().__init__(self.message)


                    @dataclass
                    class $3L($1L):
                        ""\"Error representing any unknown api errors""\"
                        code: ClassVar[str] = 'Unknown'
                        fault: ClassVar[Literal["client", "server"]] = "client"
                    """, apiError.getName(), serviceError, unknownApiError.getName());
        });
    }
}
