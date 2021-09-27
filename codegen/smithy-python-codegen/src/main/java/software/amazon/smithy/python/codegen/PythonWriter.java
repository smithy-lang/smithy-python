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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.StringJoiner;
import java.util.function.BiFunction;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolContainer;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.codegen.core.SymbolDependencyContainer;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.utils.CodeWriter;
import software.amazon.smithy.utils.StringUtils;

/**
 * Specialized code writer for managing Python dependencies.
 *
 * <p>Use the {@code $T} formatter to refer to {@link Symbol}s.
 */
public final class PythonWriter extends CodeWriter {

    private static final Logger LOGGER = Logger.getLogger(PythonWriter.class.getName());

    private final String fullPackageName;
    private final ImportDeclarations imports;
    private final List<SymbolDependency> dependencies = new ArrayList<>();

    public PythonWriter(String fullPackageName) {
        this.fullPackageName = fullPackageName;
        this.imports = new ImportDeclarations();
        trimBlankLines();
        trimTrailingSpaces();
        putFormatter('T', new PythonSymbolFormatter());
    }

    /**
     * Opens a block to write a documenation comment.
     *
     * @param runnable Runnable function to execute inside the block.
     * @return Returns the writer.
     */
    public PythonWriter openDocComment(Runnable runnable) {
        pushState("docs");
        writeInline("\"\"\"");
        runnable.run();
        write("\"\"\"");
        popState();
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
        return StringUtils.wrap(docs, CodegenUtils.MAX_PREFERRED_LINE_LENGTH - 8).replace("$", "$$");
    }

    /**
     * Opens a block to write comments.
     *
     * @param runnable Runnable function to execute inside the block.
     * @return Returns the writer.
     */
    public PythonWriter openComment(Runnable runnable) {
        pushState("docs");
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
     * Imports one or more symbols if necessary, using the name of the
     * symbol and only "USE" references.
     *
     * @param container Container of symbols to add.
     * @return Returns the writer.
     */
    public PythonWriter addUseImports(SymbolContainer container) {
        for (Symbol symbol : container.getSymbols()) {
            addImport(symbol, symbol.getName(), SymbolReference.ContextOption.USE);
        }
        return this;
    }

    /**
     * Imports a symbol reference if necessary, using the alias of the
     * reference and only associated "USE" references.
     *
     * @param symbolReference Symbol reference to import.
     * @return Returns the writer.
     */
    public PythonWriter addUseImports(SymbolReference symbolReference) {
        return addImport(symbolReference.getSymbol(), symbolReference.getAlias(), SymbolReference.ContextOption.USE);
    }

    /**
     * Imports a symbol if necessary using an alias and list of context options.
     *
     * @param symbol Symbol to optionally import.
     * @param alias The alias to refer to the symbol by.
     * @param options The list of context options (e.g., is it a USE or DECLARE symbol).
     * @return Returns the writer.
     */
    public PythonWriter addImport(Symbol symbol, String alias, SymbolReference.ContextOption... options) {
        LOGGER.finest(() -> {
            StringJoiner stackTrace = new StringJoiner("\n");
            for (StackTraceElement element : Thread.currentThread().getStackTrace()) {
                stackTrace.add(element.toString());
            }
            return String.format(
                    "Adding Python import %s as `%s` (%s); Stack trace: %s",
                    symbol, alias, Arrays.toString(options), stackTrace);
        });

        // Always add dependencies.
        dependencies.addAll(symbol.getDependencies());

        if (!symbol.getNamespace().isEmpty() && !symbol.getNamespace().equals(fullPackageName)) {
            if (symbol.getProperty("stdlib", Boolean.class).orElse(false)) {
                addStdlibImport(symbol.getName(), alias, symbol.getNamespace());
            } else {
                addImport(symbol.getName(), alias, symbol.getNamespace());
            }
        }

        // Just because the direct symbol wasn't imported doesn't mean that the
        // symbols it needs to be declared don't need to be imported.
        addImportReferences(symbol, options);

        return this;
    }

    void addImportReferences(Symbol symbol, SymbolReference.ContextOption... options) {
        for (SymbolReference reference : symbol.getReferences()) {
            for (SymbolReference.ContextOption option : options) {
                if (reference.hasOption(option)) {
                    addImport(reference.getSymbol(), reference.getAlias(), options);
                    break;
                }
            }
        }
    }

    /**
     * Imports a type using an alias from a module only if necessary.
     *
     * @param name Type to import.
     * @param as Alias to refer to the type as.
     * @param from Module to import the type from.
     * @return Returns the writer.
     */
    public PythonWriter addImport(String name, String as, String from) {
        imports.addImport(from, name, as);
        return this;
    }

    /**
     * Imports a type using an alias from the standard library only if necessary.
     *
     * @param name Type to import.
     * @param as Alias to refer to the type as.
     * @param from Module to import the type from.
     * @return Returns the writer.
     */
    public PythonWriter addStdlibImport(String name, String as, String from) {
        imports.addStdlibImport(from, name, as);
        return this;
    }

    /**
     * Adds one or more dependencies to the generated code.
     *
     * <p>The dependencies of all writers created by the {@link PythonDelegator}
     * are merged together to eventually generate a setup.py file.
     *
     * @param dependencies dependency to add.
     * @return Returns the writer.
     */
    public PythonWriter addDependency(SymbolDependencyContainer dependencies) {
        this.dependencies.addAll(dependencies.getDependencies());
        return this;
    }

    Collection<SymbolDependency> getDependencies() {
        return dependencies;
    }

    @Override
    public String toString() {
        String contents = super.toString();
        String header = "# Code generated by smithy-python-codegen DO NOT EDIT.\n\n";
        return header + imports.toString() + contents;
    }

    /**
     * Implements Python symbol formatting for the {@code $T} formatter.
     */
    private final class PythonSymbolFormatter implements BiFunction<Object, String, String> {
        @Override
        public String apply(Object type, String indent) {
            if (type instanceof Symbol) {
                Symbol typeSymbol = (Symbol) type;
                addUseImports(typeSymbol);
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
}
