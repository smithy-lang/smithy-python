/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static software.amazon.smithy.python.codegen.SymbolProperties.IMPORTABLE;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.codegen.core.SymbolWriter;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.BooleanNode;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.node.NodeVisitor;
import software.amazon.smithy.model.node.NullNode;
import software.amazon.smithy.model.node.NumberNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.StringUtils;

/**
 * Specialized code writer for managing Python dependencies.
 *
 * <p>Use the {@code $T} formatter to refer to {@link Symbol}s. The formatter writes a
 * placeholder token into the body text and records the symbol in a symbol table. At
 * {@link #toString()} time, the writer detects name collisions between imported symbols
 * and locally-defined names, aliases colliding imports with a {@code _} prefix, and
 * replaces all placeholder tokens with the resolved (possibly aliased) names.
 *
 * <p>Use the {@code $N} formatter to render {@link Node}s.
 */
@SmithyUnstableApi
public final class PythonWriter extends SymbolWriter<PythonWriter, ImportDeclarations> {

    private static final Logger LOGGER = Logger.getLogger(PythonWriter.class.getName());

    // Placeholder format: «namespace.name» — chosen to avoid conflicts with CodeFormatter's ${...} syntax.
    private static final String PLACEHOLDER_PREFIX = "\u00AB";
    private static final String PLACEHOLDER_SUFFIX = "\u00BB";

    private final String fullPackageName;
    private boolean addLogger = false;

    /**
     * Tracks all symbols referenced via {@code $T}, keyed by simple name.
     * Used to detect collisions at {@link #toString()} time.
     */
    private final Map<String, Set<Symbol>> symbolTable = new HashMap<>();

    /**
     * Names that are defined locally in this file (e.g., class names, top-level variables).
     * These take priority over imported names during collision resolution.
     */
    private final Set<String> locallyDefinedNames = new HashSet<>();

    /**
     * Constructs a PythonWriter.
     *
     * @param settings The python plugin settings.
     * @param fullPackageName The fully-qualified name of the package.
     */
    public PythonWriter(PythonSettings settings, String fullPackageName) {
        super(new ImportDeclarations(settings, fullPackageName));
        this.fullPackageName = fullPackageName;
        trimBlankLines();
        trimTrailingSpaces();
        putFormatter('T', new PythonSymbolFormatter());
        putFormatter('N', new PythonNodeFormatter(this));
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
            return new PythonWriter(settings, namespace);
        }
    }

    /**
     * Adds a top-level logger called {@code logger} to the file.
     *
     * <p>This is inserted immediately after imports.
     *
     * @return Returns the writer.
     */
    public PythonWriter addLogger() {
        addStdlibImport("logging");
        this.addLogger = true;
        return this;
    }

    /**
     * Writes single-line documentation comments from a runnable.
     *
     * @param runnable A runnable that writes single-line docs.
     * @return Returns the writer.
     */
    public PythonWriter writeSingleLineDocs(Runnable runnable) {
        pushState();
        writeInline("\"\"\"");
        runnable.run();
        trimTrailingWhitespaces();
        write("\"\"\"");
        popState();
        return this;
    }

    /**
     * Writes multi-line documentation comments from a runnable.
     *
     * @param runnable A runnable that writes multi-line docs.
     * @return Returns the writer.
     */
    public PythonWriter writeMultiLineDocs(Runnable runnable) {
        pushState();
        write("\"\"\"");
        runnable.run();
        trimTrailingWhitespaces();
        ensureNewline();
        write("\"\"\"");
        popState();
        return this;
    }

    /**
     * Writes documentation comments from a string.
     *
     * @param docs Documentation to write.
     * @param context The generation context used to determine service type and formatting.
     * @return Returns the writer.
     */
    public PythonWriter writeDocs(String docs, GenerationContext context) {
        String formatted = formatDocs(docs, context);
        if (formatted.contains("\n")) {
            writeMultiLineDocs(() -> write(formatted));
        } else {
            writeSingleLineDocs(() -> write(formatted));
        }
        return this;
    }

    /**
     * Trims all trailing whitespace from the writer buffer.
     *
     * @return Returns the writer.
     */
    public PythonWriter trimTrailingWhitespaces() {
        // Disable the writer formatting config to ensure toString()
        // returns the unmodified state of the underlying StringBuilder
        trimBlankLines(-1);
        trimTrailingSpaces(false);

        String current = super.toString();
        int end = current.length() - 1;
        while (end >= 0 && Character.isWhitespace(current.charAt(end))) {
            end--;
        }

        String trailing = current.substring(end + 1);
        if (!trailing.isEmpty()) {
            unwrite(trailing);
        }

        // Re-enable the formatting config
        trimBlankLines();
        trimTrailingSpaces(true);

        return this;
    }

    /**
     * Formats documentation from CommonMark or HTML to Google-style Markdown for Python docstrings.
     *
     * <p>For AWS services, expects HTML input. For generic clients, expects CommonMark input.
     *
     * @param docs Documentation to format.
     * @param context The generation context used to determine service type and formatting.
     * @return Formatted documentation.
     */
    public String formatDocs(String docs, GenerationContext context) {
        return MarkdownConverter.convert(docs, context);
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
        return openComment(() -> write(comment.replace("\n", " ")));
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
     * @param names Set of types to import.
     * @return Returns the writer.
     */
    public PythonWriter addStdlibImports(String namespace, Set<String> names) {
        names.forEach(name -> addStdlibImport(namespace, name));
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

    /**
     * Records a symbol as locally defined in this file (e.g., a class or top-level variable).
     *
     * <p>The writer uses this information at {@link #toString()} time to detect collisions
     * between locally-defined names and imported names. When a collision is detected, the
     * imported name is aliased with a {@code _} prefix.
     *
     * @param symbol The symbol being defined locally in this file.
     * @return Returns the writer.
     */
    public PythonWriter addLocallyDefinedSymbol(Symbol symbol) {
        locallyDefinedNames.add(symbol.getName());
        return this;
    }

    @Override
    public String toString() {
        String header = "# Code generated by smithy-python-codegen DO NOT EDIT.\n\n";
        String logger = addLogger ? "\nlogger = logging.getLogger(__name__)\n\n" : "";
        String mainContent = super.toString();

        // Resolve collisions: for each imported name that collides with a locally-defined
        // name, alias the import with a "_" prefix and rewrite placeholders in the body.
        Map<String, String> resolvedNames = resolveCollisions();

        // Replace all placeholder tokens in the body with resolved names.
        for (Map.Entry<String, String> entry : resolvedNames.entrySet()) {
            var placeholder = PLACEHOLDER_PREFIX + entry.getKey() + PLACEHOLDER_SUFFIX;
            mainContent = mainContent.replace(placeholder, entry.getValue());
        }

        String imports = getImportContainer().toString();

        return header + imports + logger + mainContent;
    }

    /**
     * Detects collisions between symbols and resolves them by aliasing.
     *
     * <p>Collision cases handled:
     * <ul>
     *   <li>Imported symbol vs locally-defined name — the import is aliased as {@code _Name}.</li>
     *   <li>Two imported symbols with the same simple name from different modules — each gets
     *       a unique alias derived from its module namespace.</li>
     *   <li>Both cases combined — locally-defined wins, all imports are aliased.</li>
     * </ul>
     *
     * @return A map from placeholder key (namespace.name) to resolved name.
     */
    private Map<String, String> resolveCollisions() {
        Map<String, String> resolvedNames = new HashMap<>();

        for (Map.Entry<String, Set<Symbol>> entry : symbolTable.entrySet()) {
            String simpleName = entry.getKey();
            Set<Symbol> symbols = entry.getValue();

            boolean collidesWithLocal = locallyDefinedNames.contains(simpleName);
            boolean hasImportCollision = symbols.size() > 1;

            if (!collidesWithLocal && !hasImportCollision) {
                // No collision — use the plain name.
                for (Symbol symbol : symbols) {
                    String placeholderKey = symbol.getNamespace() + "." + symbol.getName();
                    resolvedNames.put(placeholderKey, simpleName);
                }
                continue;
            }

            if (collidesWithLocal && !hasImportCollision) {
                // Single import collides with a locally-defined name — alias it as _Name.
                for (Symbol symbol : symbols) {
                    String placeholderKey = symbol.getNamespace() + "." + symbol.getName();
                    String aliasedName = "_" + simpleName;
                    getImportContainer().aliasImport(symbol.getNamespace(), simpleName, aliasedName);
                    resolvedNames.put(placeholderKey, aliasedName);
                }
            } else {
                // Multiple imports with the same simple name (possibly also colliding with local).
                // Each gets a unique alias derived from its module namespace.
                for (Symbol symbol : symbols) {
                    String placeholderKey = symbol.getNamespace() + "." + symbol.getName();
                    String aliasedName = buildModuleAlias(symbol);
                    getImportContainer().aliasImport(symbol.getNamespace(), simpleName, aliasedName);
                    resolvedNames.put(placeholderKey, aliasedName);
                }
            }
        }

        return resolvedNames;
    }

    /**
     * Builds a unique alias for a symbol based on its module namespace.
     *
     * <p>For example, {@code AuthOption} from {@code smithy_core.interfaces.auth} becomes
     * {@code _smithy_core_interfaces_auth_AuthOption}, and {@code AuthOption} from
     * {@code smithy_core.auth} becomes {@code _smithy_core_auth_AuthOption}.
     *
     * <p>The alias is constructed by joining all namespace segments with the symbol name.
     * This guarantees uniqueness since no two modules share the same full namespace.
     */
    private static String buildModuleAlias(Symbol symbol) {
        String namespace = symbol.getNamespace();
        String[] parts = namespace.split("\\.");
        var sb = new StringBuilder("_");
        for (String part : parts) {
            sb.append(part).append("_");
        }
        sb.append(symbol.getName());
        return sb.toString();
    }

    /**
     * Implements Python symbol formatting for the {@code $T} formatter.
     *
     * <p>Instead of returning the symbol's name directly, this formatter writes a placeholder
     * token and registers the symbol in the symbol table. The placeholder is resolved at
     * {@link PythonWriter#toString()} time, where collision detection determines the final name.
     */
    private final class PythonSymbolFormatter implements BiFunction<Object, String, String> {
        @Override
        public String apply(Object type, String indent) {
            if (type instanceof Symbol typeSymbol) {
                // If a symbol has the IMPORTABLE property set to false, don't import it and
                // treat the lack of the property being set as true
                if (typeSymbol.getProperty(IMPORTABLE).orElse(true)) {
                    addUseImports(typeSymbol);
                }
                return resolvePlaceholder(typeSymbol);
            } else if (type instanceof SymbolReference typeSymbol) {
                addImport(typeSymbol.getSymbol(), typeSymbol.getAlias(), SymbolReference.ContextOption.USE);
                return typeSymbol.getAlias();
            } else {
                throw new CodegenException(
                        "Invalid type provided to $T. Expected a Symbol, but found `" + type + "`");
            }
        }

        /**
         * Returns a placeholder token for the symbol and registers it in the symbol table.
         *
         * <p>Only symbols that are imported from another module (have a namespace but no
         * definition file) get a placeholder. Symbols without a namespace (builtins like
         * int, str, bool) and symbols with a definition file (locally-defined types) are
         * returned as-is since they don't need collision detection.
         */
        private String resolvePlaceholder(Symbol symbol) {
            if (symbol.getNamespace().isEmpty() || !symbol.getDefinitionFile().isEmpty()) {
                // No namespace means builtin. Has definition file means locally-defined.
                // Neither case needs collision detection.
                return symbol.getName();
            }

            // Register in symbol table for collision detection.
            symbolTable.computeIfAbsent(symbol.getName(), k -> new HashSet<>()).add(symbol);

            // Return a placeholder that will be resolved in toString().
            return PLACEHOLDER_PREFIX + symbol.getNamespace() + "." + symbol.getName() + PLACEHOLDER_SUFFIX;
        }
    }

    private final class PythonNodeFormatter implements BiFunction<Object, String, String> {
        private final PythonWriter writer;

        PythonNodeFormatter(PythonWriter writer) {
            this.writer = writer;
        }

        @Override
        public String apply(Object node, String indent) {
            if (node instanceof Optional<?>) {
                node = ((Optional<?>) node).get();
            }
            if (!(node instanceof Node)) {
                throw new CodegenException(
                        "Invalid type provided to $D. Expected a Node, but found `" + node + "`");
            }
            return ((Node) node).accept(new PythonNodeFormatVisitor(indent, writer));
        }
    }

    private final class PythonNodeFormatVisitor implements NodeVisitor<String> {

        private String indent;
        private final PythonWriter writer;

        PythonNodeFormatVisitor(String indent, PythonWriter writer) {
            this.indent = indent;
            this.writer = writer;
        }

        @Override
        public String booleanNode(BooleanNode node) {
            return node.getValue() ? "True" : "False";
        }

        @Override
        public String nullNode(NullNode node) {
            return "None";
        }

        @Override
        public String numberNode(NumberNode node) {
            if (node.isNaN()) {
                return "float('NaN')";
            } else if (node.isInfinite()) {
                if (node.isNegative()) {
                    return "float('-inf')";
                }
                return "float('inf')";
            } else if (node.isFloatingPointNumber()) {
                return Double.toString(node.getValue().doubleValue());
            }
            return Long.toString(node.getValue().longValue());
        }

        @Override
        public String stringNode(StringNode node) {
            return StringUtils.escapeJavaString(node.getValue(), indent);
        }

        @Override
        public String arrayNode(ArrayNode node) {
            if (node.getElements().isEmpty()) {
                return "()";
            }

            StringBuilder builder = new StringBuilder("(\n");
            var oldIndent = indent;
            indent += getIndentText();
            for (Node element : node.getElements()) {
                builder.append(indent);
                builder.append(element.accept(this));
                builder.append(",\n");
            }
            indent = oldIndent;
            builder.append(indent);
            builder.append(')');
            return builder.toString();
        }

        @Override
        public String objectNode(ObjectNode node) {
            writer.addStdlibImport("types", "MappingProxyType");
            if (node.getMembers().isEmpty()) {
                return "MappingProxyType({})";
            }

            StringBuilder builder = new StringBuilder("MappingProxyType({\n");
            var oldIndent = indent;
            indent += getIndentText();
            for (Map.Entry<StringNode, Node> member : node.getMembers().entrySet()) {
                builder.append(indent);
                builder.append(stringNode(member.getKey()));
                builder.append(": ");
                builder.append(member.getValue().accept(this));
                builder.append(",\n");
            }
            indent = oldIndent;
            builder.append(indent);
            builder.append("})");
            return builder.toString();
        }
    }
}
