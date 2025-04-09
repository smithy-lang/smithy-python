/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.List;
import java.util.Optional;

import software.amazon.smithy.model.traits.InputTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.*;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;

public class AwsRstDocFileGenerator implements PythonIntegration {

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        return List.of(
                // We generate custom RST files for each member that we want to have
                //  its own page.  This gives us much more fine-grained control of
                //  what gets generated than just using automodule or autoclass on
                //  the client would alone.
                new OperationGenerationInterceptor(context),
                new StructureGenerationInterceptor(context),
                new ErrorGenerationInterceptor(context),
                new UnionGenerationInterceptor(context),
                new UnionMemberGenerationInterceptor(context));
    }

    /**
     * Utility method to generate a header for documentation files.
     *
     * @param title The title of the section.
     * @return A formatted header string.
     */
    private static String generateHeader(String title) {
        return String.format("%s%n%s%n%n", title, "=".repeat(title.length()));
    }

    private static final class OperationGenerationInterceptor
            implements CodeInterceptor.Appender<OperationSection, PythonWriter> {

        private final GenerationContext context;

        public OperationGenerationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<OperationSection> sectionType() {
            return OperationSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, OperationSection section) {
            var operation = section.operation();
            var operationSymbol = context.symbolProvider().toSymbol(operation).expectProperty(OPERATION_METHOD);
            var input = context.model().expectShape(operation.getInputShape());
            var inputSymbol = context.symbolProvider().toSymbol(input);
            var output = context.model().expectShape(operation.getOutputShape());
            var outputSymbol = context.symbolProvider().toSymbol(output);

            String operationName = operationSymbol.getName();
            String inputSymbolName = inputSymbol.toString();
            String outputSymbolName = outputSymbol.toString();
            String serviceName = context.symbolProvider().toSymbol(section.service()).getName();
            String docsFileName = String.format("docs/client/%s.rst", operationName);
            String fullOperationReference = String.format("%s.client.%s.%s",
                    context.settings().moduleName(),
                    serviceName,
                    operationName);

            context.writerDelegator().useFileWriter(docsFileName, "", fileWriter -> {
                fileWriter.write(generateHeader(operationName));
                fileWriter.write(".. automethod:: " + fullOperationReference + "\n\n");
                fileWriter.write(".. toctree::\n    :hidden:\n    :maxdepth: 2\n\n");
                fileWriter.write("=================\nInput:\n=================\n\n");
                fileWriter.write(".. autoclass:: " + inputSymbolName + "\n    :members:\n");
                fileWriter.write("=================\nOutput:\n=================\n\n");
                if (section.isStream()) {
                    var streamShape =
                            context.model().expectShape(output.getAllMembers().get("stream").getId());
                    var streamName = context.symbolProvider().toSymbol(streamShape).toString();
                    fileWriter.write(".. autodata:: " + streamName + "  \n\n");
                } else {
                    fileWriter.write(".. autoclass:: " + outputSymbolName + "\n    " + ":members:\n\n");
                }
            });
        }
    }

    private static final class StructureGenerationInterceptor
            implements CodeInterceptor.Appender<StructureSection, PythonWriter> {

        private final GenerationContext context;

        public StructureGenerationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<StructureSection> sectionType() {
            return StructureSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, StructureSection section) {
            var shape = section.structure();
            var symbol = context.symbolProvider().toSymbol(shape);
            String docsFileName = String.format("docs/models/%s.rst",
                    symbol.getName());

            boolean isStreaming = Optional.ofNullable(shape.getAllMembers().get("body"))
                    .map(member -> context.model().expectShape(member.getTarget()))
                    .map(memberShape -> memberShape.hasTrait(StreamingTrait.class))
                    .orElse(false);            // Input and output shapes are typically skipped since they are generated
            // Input and output shapes are typically skipped since they are generated
            // on the operation's page. The exception to this is the output of
            // streaming operations where we have a different output shape defined.
            if (!shape.hasTrait(InputTrait.class) && !shape.hasTrait(OutputTrait.class) || isStreaming) {
                context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                    writer.write(generateHeader(symbol.getName()));
                    writer.write(".. autoclass:: " + symbol.toString() + "\n   :members:\n");
                });
            }
        }
    }

    private static final class ErrorGenerationInterceptor
            implements CodeInterceptor.Appender<ErrorSection, PythonWriter> {

        private final GenerationContext context;

        public ErrorGenerationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<ErrorSection> sectionType() {
            return ErrorSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, ErrorSection section) {
            var symbol = section.errorSymbol();
            String docsFileName = String.format("docs/models/%s.rst",
                    symbol.getName());
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write(generateHeader(symbol.getName()));
                writer.write(".. autoexception:: " + symbol.toString() + "\n   :members:\n   :show-inheritance:\n");
            });
        }
    }

    private static final class UnionGenerationInterceptor
            implements CodeInterceptor.Appender<UnionSection, PythonWriter> {

        private final GenerationContext context;

        public UnionGenerationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<UnionSection> sectionType() {
            return UnionSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, UnionSection section) {
            String parentName = section.parentName();
            String docsFileName = String.format("docs/models/%s.rst", parentName);
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write(".. _" + parentName + ":\n\n");
                writer.write(generateHeader(parentName));
                writer.write(
                        ".. autodata:: " + context.symbolProvider().toSymbol(section.unionShape()).toString() + "  \n");
            });
        }
    }

    private static final class UnionMemberGenerationInterceptor
            implements CodeInterceptor.Appender<UnionMemberSection, PythonWriter> {

        private final GenerationContext context;

        public UnionMemberGenerationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<UnionMemberSection> sectionType() {
            return UnionMemberSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, UnionMemberSection section) {
            var memberSymbol = section.memberSymbol();
            String symbolName = memberSymbol.getName();
            String docsFileName = String.format("docs/models/%s.rst", symbolName);
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write(".. _" + symbolName + ":\n\n");
                writer.write(generateHeader(symbolName));
                writer.write(".. autoclass:: " + memberSymbol.toString() + "  \n");
            });
        }
    }
}
