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

import java.util.Set;
import java.util.function.BiFunction;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.codegen.core.SymbolWriter;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.StringUtils;

/**
 * Specialized code writer for managing Python dependencies.
 *
 * <p>Use the {@code $T} formatter to refer to {@link Symbol}s.
 */
@SmithyUnstableApi
public final class PythonWriter extends SymbolWriter<PythonWriter, ImportDeclarations> {

    private static final Logger LOGGER = Logger.getLogger(PythonWriter.class.getName());

    private final String fullPackageName;
    private final boolean addCodegenWarningHeader;

    /**
     * Constructs a PythonWriter.
     *
     * @param settings The python plugin settings.
     * @param fullPackageName The fully-qualified name of the package.
     */
    public PythonWriter(PythonSettings settings, String fullPackageName) {
        this(settings, fullPackageName, true);
    }

    /**
     * Constructs a PythonWriter.
     *
     * @param settings The python plugin settings.
     * @param fullPackageName The fully-qualified name of the package.
     * @param addCodegenWarningHeader Whether to add a header comment warning that the file is code generated.
     */
    public PythonWriter(PythonSettings settings, String fullPackageName, boolean addCodegenWarningHeader) {
        super(new ImportDeclarations(settings, fullPackageName));
        this.fullPackageName = fullPackageName;
        trimBlankLines();
        trimTrailingSpaces();
        putFormatter('T', new PythonSymbolFormatter());
        this.addCodegenWarningHeader = addCodegenWarningHeader;
    }

    /**
     * A factory class to create {@link PythonWriter}s.
     */
    public static final class PythonWriterFactory implements SymbolWriter.Factory<PythonWriter> {

        private final PythonSettings settings;

        /**
         * @param settings The python plugin settings.
         */
        public PythonWriterFactory(PythonSettings settings) {
            this.settings = settings;
        }

        @Override
        public PythonWriter apply(String filename, String namespace) {
            // Markdown doesn't have comments, so there's no non-intrusive way to
            // add the warning.
            var addWarningHeader = !filename.endsWith(".md");
            return new PythonWriter(settings, namespace, addWarningHeader);
        }
    }

    /**
     * Writes documentation comments from a runnable.
     *
     * @param runnable A runnable that writes docs.
     * @return Returns the writer.
     */
    public PythonWriter writeDocs(Runnable runnable) {
        pushState();
        writeInline("\"\"\"");
        runnable.run();
        write("\"\"\"");
        popState();
        return this;
    }

    /**
     * Writes documentation comments from a string.
     *
     * @param docs Documentation to write.
     * @return Returns the writer.
     */
    public PythonWriter writeDocs(String docs) {
        writeDocs(() -> write(formatDocs(docs)));
        return this;
    }

    /**
     * Formats a given Commonmark string and wraps it for use in a doc
     * comment.
     *
     * @param docs Documentation to format.
     * @return Formatted documentation.
     */
    public String formatDocs(String docs) {
        // TODO: write a documentation converter to convert markdown to rst
        return StringUtils.wrap(docs, CodegenUtils.MAX_PREFERRED_LINE_LENGTH - 8)
                .replace("$", "$$");
    }

    /**
     * Opens a block to write comments.
     *
     * @param runnable Runnable function to execute inside the block.
     * @return Returns the writer.
     */
    public PythonWriter openComment(Runnable runnable) {
        pushState();
        setNewlinePrefix("# ");
        runnable.run();
        setNewlinePrefix("");
        popState();
        return this;
    }

    /**
     * Writes a comment from a string.
     *
     * @param comment The comment to write.
     * @return Returns the writer.
     */
    public PythonWriter writeComment(String comment) {
        return openComment(() -> write(formatDocs(comment.replace("\n", " "))));
    }


    /**
     * Imports a module from the standard library without an alias.
     *
     * @param namespace Module to import.
     * @return Returns the writer.
     */
    public PythonWriter addStdlibImport(String namespace) {
        getImportContainer().addStdlibImport(namespace);
        return this;
    }

    /**
     * Imports a type using an alias from the standard library only if necessary.
     *
     * @param namespace Module to import the type from.
     * @param name Type to import.
     * @return Returns the writer.
     */
    public PythonWriter addStdlibImport(String namespace, String name) {
        getImportContainer().addStdlibImport(namespace, name);
        return this;
    }

    /**
     * Imports a type using an alias from the standard library only if necessary.
     *
     * @param namespace Module to import the type from.
     * @param name Type to import.
     * @param alias The name to import the type as.
     * @return Returns the writer.
     */
    public PythonWriter addStdlibImport(String namespace, String name, String alias) {
        getImportContainer().addStdlibImport(namespace, name, alias);
        return this;
    }

    /**
     * Imports a type using an alias from a module only if necessary.
     *
     * <p>If you use this, you MUST add the dependency manually using {@link PythonWriter#addDependency}.
     *
     * @param namespace Module to import the type from.
     * @param name Type to import.
     * @return Returns the writer.
     */
    public PythonWriter addImport(String namespace, String name) {
        getImportContainer().addImport(namespace, name, name);
        return this;
    }

    /**
     * Imports a type using an alias from a module only if necessary.
     *
     * <p>If you use this, you MUST add the dependency manually using {@link PythonWriter#addDependency}.
     *
     * @param namespace Module to import the type from.
     * @param name Type to import.
     * @param alias The name to import the type as.
     * @return Returns the writer.
     */
    public PythonWriter addImport(String namespace, String name, String alias) {
        getImportContainer().addImport(namespace, name, alias);
        return this;
    }

    /**
     * Imports a set of types from a module only if necessary.
     *
     * @param namespace Module to import the type from.
     * @param names Set of types to import.
     * @return Returns the writer.
     */
    public PythonWriter addImports(String namespace, Set<String> names) {
        names.forEach((name) -> getImportContainer().addImport(namespace, name, name));
        return this;
    }

    /**
     * Conditionally write text.
     *
     * <p>Useful for short-handing a conditional write when
     * you aren't able to use the built-in conditional
     * formatting functionality.
     *
     * @param shouldWrite Whether to write the text or not.
     * @param content Content to write.
     * @param args String arguments to use for formatting.
     * @return Returns self.
     */
    public PythonWriter maybeWrite(boolean shouldWrite, Object content, Object... args) {
        if (shouldWrite) {
            write(content, args);
        }
        return this;
    }

    @Override
    public String toString() {
        String contents = getImportContainer().toString() + super.toString();
        if (addCodegenWarningHeader) {
            String header = "# Code generated by smithy-python-codegen DO NOT EDIT.\n\n";
            contents = header + contents;
        }
        return contents;
    }

    /**
     * Implements Python symbol formatting for the {@code $T} formatter.
     */
    private final class PythonSymbolFormatter implements BiFunction<Object, String, String> {
        @Override
        public String apply(Object type, String indent) {
            if (type instanceof Symbol) {
                Symbol typeSymbol = (Symbol) type;
                // Check if the symbol is an operation - we shouldn't add imports for operations, since
                //  they are methods of the service object and *can't* be imported
                if (!isOperationSymbol(typeSymbol)) {
                    addUseImports(typeSymbol);
                }
                return typeSymbol.getName();
            } else if (type instanceof SymbolReference) {
                SymbolReference typeSymbol = (SymbolReference) type;
                addImport(typeSymbol.getSymbol(), typeSymbol.getAlias(), SymbolReference.ContextOption.USE);
                return typeSymbol.getAlias();
            } else {
                throw new CodegenException(
                        "Invalid type provided to $T. Expected a Symbol, but found `" + type + "`");
            }
        }
    }

    private Boolean isOperationSymbol(Symbol typeSymbol) {
        return typeSymbol.getProperty("shape", Shape.class).map(Shape::isOperationShape).orElse(false);
    }
}
