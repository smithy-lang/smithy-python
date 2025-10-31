/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.ArrayList;
import java.util.List;
import java.util.TreeSet;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.traits.InputTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.model.traits.TitleTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.*;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;

/**
 * Generates API Reference stub files in Markdown for MkDocs/mkdocstrings doc gen.
 *
 * This integration creates individual .md files for operations, structures, errors,
 * unions, and enums that are used with MkDocs and mkdocstrings to generate documentation.
 * It also generates a comprehensive index.md that documents the client and config objects,
 * along with lists of all available client operations and models.
 */
public class AwsMkDocsFileGenerator implements PythonIntegration {

    // Shared collections to track what we've generated
    private final TreeSet<String> operations = new TreeSet<>();
    private final TreeSet<String> structures = new TreeSet<>();
    private final TreeSet<String> errors = new TreeSet<>();
    private final TreeSet<String> enums = new TreeSet<>();
    private final TreeSet<String> unions = new TreeSet<>();

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        if (!CodegenUtils.isAwsService(context)) {
            return List.of();
        }
        var interceptors = new ArrayList<CodeInterceptor<? extends CodeSection, PythonWriter>>();
        interceptors.add(new OperationGenerationInterceptor(context, operations));
        interceptors.add(new StructureGenerationInterceptor(context, structures));
        interceptors.add(new ErrorGenerationInterceptor(context, errors));
        interceptors.add(new EnumGenerationInterceptor(context, enums));
        interceptors.add(new IntEnumGenerationInterceptor(context, enums));
        interceptors.add(new UnionGenerationInterceptor(context, unions));
        return interceptors;
    }

    @Override
    public void customize(GenerationContext context) {
        if (!CodegenUtils.isAwsService(context)) {
            return;
        }
        // This runs after shape generation, so we can now generate the index with all collected operations/models
        new IndexGenerator(context, operations, structures, errors, enums, unions).run();
    }

    /**
     * Utility method to generate a header for documentation files.
     *
     * @param title The title of the section.
     * @return A formatted header string.
     */
    private static String generateHeader(String title) {
        return String.format("# %s%n%n", title);
    }

    private static final class OperationGenerationInterceptor
            implements CodeInterceptor.Appender<OperationSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> operations;

        public OperationGenerationInterceptor(
                GenerationContext context,
                TreeSet<String> operations
        ) {
            this.context = context;
            this.operations = operations;
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
            String clientName = context.symbolProvider().toSymbol(section.service()).getName();
            String docsFileName = String.format("docs/operations/%s.md", operationName);
            String fullOperationReference = String.format("%s.client.%s.%s",
                    context.settings().moduleName(),
                    clientName,
                    operationName);

            // Track this operation
            operations.add(operationName);

            context.writerDelegator().useFileWriter(docsFileName, "", fileWriter -> {
                fileWriter.write(generateHeader(operationName));

                fileWriter.write("\n## Operation\n\n");
                fileWriter.write("::: " + fullOperationReference);
                fileWriter.write("""
                            options:
                                heading_level: 3
                        """);

                // Add Input Structure documentation
                fileWriter.write("\n## Input\n\n");
                fileWriter.write("::: " + inputSymbol.toString());
                fileWriter.write("""
                            options:
                                heading_level: 3
                        """);

                // Add Output Structure documentation
                fileWriter.write("\n## Output\n\n");

                // Check if operation returns event streams
                var eventStreamIndex = EventStreamIndex.of(context.model());
                var inputStreamInfo = eventStreamIndex.getInputInfo(operation);
                var outputStreamInfo = eventStreamIndex.getOutputInfo(operation);
                boolean hasInputStream = inputStreamInfo.isPresent();
                boolean hasOutputStream = outputStreamInfo.isPresent();

                if (hasInputStream && hasOutputStream) {
                    // Duplex event stream
                    var inputStreamTarget = inputStreamInfo.get().getEventStreamTarget();
                    var inputStreamShape = context.model().expectShape(inputStreamTarget.getId());
                    var inputStreamSymbol = context.symbolProvider().toSymbol(inputStreamShape);

                    var outputStreamTarget = outputStreamInfo.get().getEventStreamTarget();
                    var outputStreamShape = context.model().expectShape(outputStreamTarget.getId());
                    var outputStreamSymbol = context.symbolProvider().toSymbol(outputStreamShape);

                    fileWriter.write("This operation returns a `DuplexEventStream` for bidirectional streaming.\n\n");
                    fileWriter.write("### Event Stream Structure\n\n");
                    fileWriter.write("#### Input Event Type\n\n");
                    fileWriter.write("[`$L`](../unions/$L.md)\n\n",
                            inputStreamSymbol.getName(),
                            inputStreamSymbol.getName());
                    fileWriter.write("#### Output Event Type\n\n");
                    fileWriter.write("[`$L`](../unions/$L.md)\n\n",
                            outputStreamSymbol.getName(),
                            outputStreamSymbol.getName());
                    fileWriter.write("### Initial Response Structure\n\n");
                } else if (hasInputStream) {
                    // Input event stream
                    var streamTarget = inputStreamInfo.get().getEventStreamTarget();
                    var streamShape = context.model().expectShape(streamTarget.getId());
                    var streamSymbol = context.symbolProvider().toSymbol(streamShape);

                    fileWriter
                            .write("This operation returns an `InputEventStream` for client-to-server streaming.\n\n");
                    fileWriter.write("### Event Stream Structure\n\n");
                    fileWriter.write("#### Input Event Type\n\n");
                    fileWriter.write("[`$L`](../unions/$L.md)\n\n",
                            streamSymbol.getName(),
                            streamSymbol.getName());
                    fileWriter.write("### Final Response Structure\n\n");
                } else if (hasOutputStream) {
                    var streamTarget = outputStreamInfo.get().getEventStreamTarget();
                    var streamShape = context.model().expectShape(streamTarget.getId());
                    var streamSymbol = context.symbolProvider().toSymbol(streamShape);

                    fileWriter
                            .write("This operation returns an `OutputEventStream` for server-to-client streaming.\n\n");
                    fileWriter.write("### Event Stream Structure\n\n");
                    fileWriter.write("#### Output Event Type\n\n");
                    fileWriter.write("[`$L`](../unions/$L.md)\n\n",
                            streamSymbol.getName(),
                            streamSymbol.getName());
                    fileWriter.write("### Initial Response Structure\n\n");
                }

                fileWriter.write("::: " + outputSymbol.toString());
                // Use heading level 4 for event streams, level 3 for regular operations
                int headingLevel = (hasInputStream || hasOutputStream) ? 4 : 3;
                fileWriter.write("""
                            options:
                                heading_level: $L
                        """, headingLevel);

                // Add Errors documentation
                var operationErrors = operation.getErrorsSet();
                if (!operationErrors.isEmpty()) {
                    fileWriter.write("\n## Errors\n\n");
                    for (var errorId : operationErrors) {
                        var errorShape = context.model().expectShape(errorId);
                        var errorSymbol = context.symbolProvider().toSymbol(errorShape);
                        String errorName = errorSymbol.getName();
                        fileWriter.write("- [`$L`](../errors/$L.md)\n", errorName, errorName);
                    }
                }
            });
        }
    }

    private static final class StructureGenerationInterceptor
            implements CodeInterceptor.Appender<StructureSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> structures;

        public StructureGenerationInterceptor(GenerationContext context, TreeSet<String> structures) {
            this.context = context;
            this.structures = structures;
        }

        @Override
        public Class<StructureSection> sectionType() {
            return StructureSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, StructureSection section) {
            var shape = section.structure();
            var symbol = context.symbolProvider().toSymbol(shape);
            String symbolName = symbol.getName();
            String docsFileName = String.format("docs/structures/%s.md", symbolName);
            // Don't generate separate docs for input/output structures (they're included with operations)
            if (!shape.hasTrait(InputTrait.class) && !shape.hasTrait(OutputTrait.class)) {
                structures.add(symbolName);
                context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                    writer.write("::: " + symbol.toString());
                    writer.write("""
                                options:
                                    heading_level: 1
                            """);
                });
            }
        }
    }

    private static final class ErrorGenerationInterceptor
            implements CodeInterceptor.Appender<ErrorSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> errors;

        public ErrorGenerationInterceptor(GenerationContext context, TreeSet<String> errors) {
            this.context = context;
            this.errors = errors;
        }

        @Override
        public Class<ErrorSection> sectionType() {
            return ErrorSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, ErrorSection section) {
            var symbol = section.errorSymbol();
            String symbolName = symbol.getName();
            String docsFileName = String.format("docs/errors/%s.md", symbolName);
            errors.add(symbolName);
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write("::: " + symbol.toString());
                writer.write("""
                            options:
                                heading_level: 1
                        """);
            });
        }
    }

    private static final class EnumGenerationInterceptor
            implements CodeInterceptor.Appender<EnumSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> enums;

        public EnumGenerationInterceptor(GenerationContext context, TreeSet<String> enums) {
            this.context = context;
            this.enums = enums;
        }

        @Override
        public Class<EnumSection> sectionType() {
            return EnumSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, EnumSection section) {
            var symbol = section.enumSymbol();
            String symbolName = symbol.getName();
            String docsFileName = String.format("docs/enums/%s.md", symbolName);
            enums.add(symbolName);
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write("::: " + symbol.toString());
                writer.write("""
                            options:
                                heading_level: 1
                                members: true
                        """);
            });
        }
    }

    private static final class IntEnumGenerationInterceptor
            implements CodeInterceptor.Appender<IntEnumSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> enums;

        public IntEnumGenerationInterceptor(GenerationContext context, TreeSet<String> enums) {
            this.context = context;
            this.enums = enums;
        }

        @Override
        public Class<IntEnumSection> sectionType() {
            return IntEnumSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, IntEnumSection section) {
            var symbol = section.enumSymbol();
            String symbolName = symbol.getName();
            String docsFileName = String.format("docs/enums/%s.md", symbolName);
            enums.add(symbolName);
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                writer.write("::: " + symbol.toString());
                writer.write("""
                            options:
                                heading_level: 1
                                members: true
                        """);
            });
        }
    }

    private static final class UnionGenerationInterceptor
            implements CodeInterceptor.Appender<UnionSection, PythonWriter> {

        private final GenerationContext context;
        private final TreeSet<String> unions;

        public UnionGenerationInterceptor(
                GenerationContext context,
                TreeSet<String> unions
        ) {
            this.context = context;
            this.unions = unions;
        }

        @Override
        public Class<UnionSection> sectionType() {
            return UnionSection.class;
        }

        @Override
        public void append(PythonWriter pythonWriter, UnionSection section) {
            String parentName = section.parentName();

            String docsFileName = String.format("docs/unions/%s.md", parentName);
            unions.add(parentName);
            var unionSymbol = context.symbolProvider().toSymbol(section.unionShape());
            context.writerDelegator().useFileWriter(docsFileName, "", writer -> {
                // Document the union type alias
                writer.write("::: " + unionSymbol.toString());
                writer.write("""
                            options:
                                heading_level: 1
                        """);

                // Document each union member on the same page
                writer.write("\n## Union Members\n\n");
                for (var member : section.unionShape().members()) {
                    var memberSymbol = context.symbolProvider().toSymbol(member);
                    writer.write("::: " + memberSymbol.toString());
                    writer.write("""
                                options:
                                    heading_level: 3
                            """);
                }

                // Document the unknown variant
                var unknownSymbol = unionSymbol
                        .expectProperty(software.amazon.smithy.python.codegen.SymbolProperties.UNION_UNKNOWN);
                writer.write("::: " + unknownSymbol.toString());
                writer.write("""
                            options:
                                heading_level: 3
                        """);
            });
        }
    }

    /**
     * Generates the main index.md file and config documentation after all shapes are generated.
     */
    private static final class IndexGenerator implements Runnable {

        private final GenerationContext context;
        private final TreeSet<String> operations;
        private final TreeSet<String> structures;
        private final TreeSet<String> errors;
        private final TreeSet<String> enums;
        private final TreeSet<String> unions;

        public IndexGenerator(
                GenerationContext context,
                TreeSet<String> operations,
                TreeSet<String> structures,
                TreeSet<String> errors,
                TreeSet<String> enums,
                TreeSet<String> unions
        ) {
            this.context = context;
            this.operations = operations;
            this.structures = structures;
            this.errors = errors;
            this.enums = enums;
            this.unions = unions;
        }

        @Override
        public void run() {
            var service = context.model().expectShape(context.settings().service());
            String clientName = context.symbolProvider().toSymbol(service).getName();
            String title = service.getTrait(ServiceTrait.class)
                    .map(ServiceTrait::getSdkId)
                    .orElseGet(() -> service.getTrait(TitleTrait.class)
                            .map(StringTrait::getValue)
                            .orElse(clientName));
            String moduleName = context.settings().moduleName();

            // Generate main index.md
            context.writerDelegator().useFileWriter("docs/index.md", "", indexWriter -> {
                indexWriter.write("# $L\n\n", title);

                // Client section 
                indexWriter.write("\n## Client\n\n");
                indexWriter.write("::: $L.client.$L", moduleName, clientName);
                indexWriter.write("""
                            options:
                                merge_init_into_class: true
                                docstring_options:
                                    ignore_init_summary: true
                                members: false
                                heading_level: 3
                        """);

                // Operations section
                indexWriter.write("\n## Available Operations\n\n");
                for (String operation : operations) {
                    indexWriter.write("- [`$L`](operations/$L.md)\n", operation, operation);
                }

                // Config section
                indexWriter.write("\n## Configuration\n\n");
                indexWriter.write("::: $L.config.Config", moduleName);
                indexWriter.write("""
                            options:
                                merge_init_into_class: true
                                docstring_options:
                                    ignore_init_summary: true
                                heading_level: 3
                        """);

                // Errors section
                if (!errors.isEmpty()) {
                    indexWriter.write("\n## Errors\n\n");
                    for (String error : errors) {
                        indexWriter.write("- [`$L`](errors/$L.md)\n", error, error);
                    }
                }

                // Structures section
                if (!structures.isEmpty()) {
                    indexWriter.write("\n## Structures\n\n");
                    for (String structure : structures) {
                        indexWriter.write("- [`$L`](structures/$L.md)\n", structure, structure);
                    }
                }

                // Unions section
                if (!unions.isEmpty()) {
                    indexWriter.write("\n## Unions\n\n");
                    for (String union : unions) {
                        indexWriter.write("- [`$L`](unions/$L.md)\n", union, union);
                    }
                }

                // Enums section
                if (!enums.isEmpty()) {
                    indexWriter.write("\n## Enums\n\n");
                    for (String enumName : enums) {
                        indexWriter.write("- [`$L`](enums/$L.md)\n", enumName, enumName);
                    }
                }
            });

            // Generate custom CSS file to widen content area width
            context.writerDelegator().useFileWriter("docs/stylesheets/extra.css", "", cssWriter -> {
                cssWriter.write("""
                        .md-grid {
                          max-width: 70rem;
                        }
                        """);
            });
        }
    }
}
