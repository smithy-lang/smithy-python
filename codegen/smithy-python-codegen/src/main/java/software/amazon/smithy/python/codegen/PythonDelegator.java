/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.Shape;

/**
 * Manages writers for Python files.
 */
final class PythonDelegator {

    private final PythonSettings settings;
    private final Model model;
    private final FileManifest fileManifest;
    private final SymbolProvider symbolProvider;
    private final Map<String, PythonWriter> writers = new HashMap<>();

    PythonDelegator(PythonSettings settings, Model model, FileManifest fileManifest, SymbolProvider symbolProvider) {
        this.settings = settings;
        this.model = model;
        this.fileManifest = fileManifest;
        this.symbolProvider = symbolProvider;
    }

    /**
     * Writes all pending writers to disk and then clears them out.
     */
    void flushWriters() {
        writers.forEach((filename, writer) -> fileManifest.writeFile(filename, writer.toString()));
        writers.clear();
    }

    /**
     * Gets a previously created writer or creates a new one if needed.
     *
     * @param shape Shape to create the writer for.
     * @param writerConsumer Consumer that accepts and works with the file.
     */
    void useShapeWriter(Shape shape, Consumer<PythonWriter> writerConsumer) {
        Symbol symbol = symbolProvider.toSymbol(shape);
        String namespace = symbol.getNamespace();
        if (namespace.equals(".")) {
            namespace = CodegenUtils.getDefaultPackageImportName(settings.getModuleName());
        }
        PythonWriter writer = checkoutWriter(symbol.getDefinitionFile(), namespace);

        writer.pushState();
        writerConsumer.accept(writer);
        writer.popState();
    }

    /**
     * Gets a previously created writer or creates a new one if needed
     * and adds a new line if the writer already exists.
     *
     * @param filename       Name of the file to create.
     * @param writerConsumer Consumer that accepts and works with the file.
     */
    void useFileWriter(String filename, String namespace, Consumer<PythonWriter> writerConsumer) {
        writerConsumer.accept(checkoutWriter(filename, namespace));
    }

    private PythonWriter checkoutWriter(String filename, String namespace) {
        String formattedFilename = Paths.get(filename).normalize().toString();
        boolean needsNewline = writers.containsKey(formattedFilename);

        PythonWriter writer = writers.computeIfAbsent(formattedFilename, f -> new PythonWriter(namespace));

        if (needsNewline) {
            writer.write("\n");
        }

        return writer;
    }
}
