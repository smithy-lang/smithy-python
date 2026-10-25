/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import java.util.Comparator;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.ImportContainer;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.utils.SmithyInternalApi;
import software.amazon.smithy.utils.StringUtils;

/**
 * Internal class used for aggregating imports of a file.
 */
@SmithyInternalApi
public final class ImportDeclarations implements ImportContainer {
    private static final String MODULE_IMPORT_TEMPLATE = "import %s%n";
    // Relative imports sort last inside the TYPE_CHECKING block, as they do outside it.
    private static final Comparator<String> TYPE_CHECKING_ORDER =
            Comparator.comparing((String namespace) -> namespace.startsWith("."))
                    .thenComparing(Comparator.naturalOrder());

    private final Map<String, Map<String, String>> stdlibImports = new TreeMap<>();
    private final Map<String, Map<String, String>> externalImports = new TreeMap<>();
    private final Map<String, Map<String, String>> localImports = new TreeMap<>();
    // Imports emitted inside `if TYPE_CHECKING:` -- used only in annotations, never at
    // runtime. Requires `from __future__ import annotations` so annotations stay strings.
    private final Map<String, Map<String, String>> typeCheckingImports = new TreeMap<>(TYPE_CHECKING_ORDER);
    private boolean futureAnnotations = false;

    private final PythonSettings settings;
    private final String localNamespace;

    ImportDeclarations(PythonSettings settings, String namespace) {
        this.settings = settings;
        this.localNamespace = namespace;
    }

    @Override
    public void importSymbol(Symbol symbol, String alias) {
        if (!symbol.getNamespace().isEmpty() && !symbol.getNamespace().equals(localNamespace)) {
            if (symbol.getProperty(SymbolProperties.STDLIB).orElse(false)) {
                addStdlibImport(symbol.getNamespace(), symbol.getName(), alias);
            } else {
                addImport(symbol.getNamespace(), symbol.getName(), alias);
            }
        }
    }

    /**
     * Imports a symbol inside {@code if TYPE_CHECKING:}, skipping builtins and symbols
     * defined in this file as {@link #importSymbol} does.
     *
     * @param symbol The symbol to import.
     * @param alias The name to import the symbol as.
     */
    public void importTypeCheckingSymbol(Symbol symbol, String alias) {
        if (!symbol.getNamespace().isEmpty() && !symbol.getNamespace().equals(localNamespace)) {
            addTypeCheckingImport(symbol.getNamespace(), symbol.getName(), alias);
        }
    }

    public ImportDeclarations addImport(String namespace, String name, String alias) {
        if (namespace.startsWith(settings.moduleName())) {
            return addImportToMap(importKey(namespace), name, alias, localImports);
        }
        return addImportToMap(namespace, name, alias, externalImports);
    }

    /** Enable `from __future__ import annotations` so annotations are deferred strings. */
    public void enableFutureAnnotations() {
        this.futureAnnotations = true;
    }

    /** Add an import that is emitted only inside `if TYPE_CHECKING:` (annotation-only). */
    public ImportDeclarations addTypeCheckingImport(String namespace, String name, String alias) {
        enableFutureAnnotations();
        return addImportToMap(importKey(namespace), name, alias, typeCheckingImports);
    }

    // The key an import's namespace is stored under: relative within the package, except
    // in test modules, where Python rejects relative imports beyond the top-level package.
    private String importKey(String namespace) {
        if (namespace.startsWith(settings.moduleName()) && !localNamespace.startsWith("tests")) {
            return relativize(namespace);
        }
        return namespace;
    }

    private String relativize(String namespace) {
        if (namespace.startsWith(localNamespace)) {
            return "." + namespace.substring(localNamespace.length());
        }
        var localParts = localNamespace.split("\\.");
        var parts = namespace.split("\\.");
        int commonSegments = 0;
        for (; commonSegments < Math.min(localParts.length, parts.length); commonSegments++) {
            if (!parts[commonSegments].equals(localParts[commonSegments])) {
                break;
            }
        }
        var prefix = StringUtils.repeat(".", localParts.length - commonSegments);
        String[] segments = namespace.split("\\.", commonSegments + 1);
        if (commonSegments >= segments.length) {
            return ".";
        } else {
            return prefix + segments[commonSegments];
        }
    }

    ImportDeclarations addStdlibImport(String namespace) {
        return addStdlibImport(namespace, "", "");
    }

    ImportDeclarations addStdlibImport(String namespace, String name) {
        return addStdlibImport(namespace, name, name);
    }

    ImportDeclarations addStdlibImport(String namespace, String name, String alias) {
        return addImportToMap(namespace, name, alias, stdlibImports);
    }

    private ImportDeclarations addImportToMap(
            String namespace,
            String name,
            String alias,
            Map<String, Map<String, String>> importMap
    ) {
        if (name.equals("*")) {
            throw new CodegenException("Wildcard imports are forbidden.");
        }
        Map<String, String> namespaceImports = importMap.computeIfAbsent(namespace, ns -> new TreeMap<>());
        namespaceImports.put(name, alias);
        return this;
    }

    /**
     * Retroactively aliases an existing import to avoid name collisions.
     *
     * <p>This is called by {@link PythonWriter} at {@code toString()} time when a collision
     * is detected. The import statement is rewritten from {@code from namespace import name}
     * to {@code from namespace import name as alias}.
     *
     * <p>The lookup mirrors the dispatch logic in {@link #addImport} so that aliasing works
     * for every import map:
     * <ul>
     *   <li>{@code stdlibImports} — keyed by absolute namespace.</li>
     *   <li>{@code externalImports} — keyed by absolute namespace.</li>
     *   <li>{@code localImports} — keyed by {@code importKey}, relative for same-package imports.</li>
     *   <li>{@code typeCheckingImports} — keyed by {@code importKey}.</li>
     * </ul>
     *
     * @param namespace The module namespace of the import (absolute).
     * @param name The original imported name.
     * @param alias The alias to use instead.
     */
    void aliasImport(String namespace, String name, String alias) {
        // stdlib imports are stored with absolute namespaces.
        aliasImportInMap(namespace, name, alias, stdlibImports);

        // external imports are stored with absolute namespaces.
        aliasImportInMap(namespace, name, alias, externalImports);

        // local and type-checking imports are keyed by importKey, as their add methods store them.
        var key = importKey(namespace);
        aliasImportInMap(key, name, alias, localImports);
        aliasImportInMap(key, name, alias, typeCheckingImports);
    }

    private void aliasImportInMap(
            String namespace,
            String name,
            String alias,
            Map<String, Map<String, String>> importMap
    ) {
        var namespaceImports = importMap.get(namespace);
        if (namespaceImports != null
                && namespaceImports.containsKey(name)
                && namespaceImports.get(name).equals(name)) {
            namespaceImports.put(name, alias);
        }
    }

    @Override
    public String toString() {
        if (externalImports.isEmpty() && stdlibImports.isEmpty()
                && localImports.isEmpty()
                && typeCheckingImports.isEmpty()) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        if (futureAnnotations) {
            builder.append("from __future__ import annotations\n\n");
        }
        if (!stdlibImports.isEmpty()) {
            formatImportList(builder, stdlibImports);
        }
        if (!externalImports.isEmpty()) {
            formatImportList(builder, externalImports);
        }
        if (!localImports.isEmpty()) {
            formatImportList(builder, localImports);
        }
        var typeCheckingOnlyImports = withoutRuntimeImports(typeCheckingImports);
        if (!typeCheckingOnlyImports.isEmpty()) {
            builder.append("from typing import TYPE_CHECKING\n\n");
            builder.append("if TYPE_CHECKING:\n");
            var block = new StringBuilder();
            formatImportList(block, typeCheckingOnlyImports);
            // indent the rendered imports into the TYPE_CHECKING block
            for (var line : block.toString().split("\n", -1)) {
                if (line.isEmpty()) {
                    builder.append("\n");
                } else {
                    builder.append("    ").append(line).append("\n");
                }
            }
        }
        builder.append("\n");
        return builder.toString();
    }

    // A name the file already imports at runtime is usable in annotations as-is.
    private Map<String, Map<String, String>> withoutRuntimeImports(Map<String, Map<String, String>> importMap) {
        Map<String, Map<String, String>> result = new TreeMap<>(TYPE_CHECKING_ORDER);
        for (var namespaceEntry : importMap.entrySet()) {
            var namespace = namespaceEntry.getKey();
            for (var nameEntry : namespaceEntry.getValue().entrySet()) {
                var name = nameEntry.getKey();
                if (isRuntimeImport(namespace, name, stdlibImports)
                        || isRuntimeImport(namespace, name, externalImports)
                        || isRuntimeImport(namespace, name, localImports)) {
                    continue;
                }
                result.computeIfAbsent(namespace, ns -> new TreeMap<>()).put(name, nameEntry.getValue());
            }
        }
        return result;
    }

    private static boolean isRuntimeImport(
            String namespace,
            String name,
            Map<String, Map<String, String>> importMap
    ) {
        var namespaceImports = importMap.get(namespace);
        return namespaceImports != null && namespaceImports.containsKey(name);
    }

    private void formatImportList(StringBuilder builder, Map<String, Map<String, String>> importMap) {
        for (Map.Entry<String, Map<String, String>> namespaceEntry : importMap.entrySet()) {
            if (namespaceEntry.getValue().remove("") != null) {
                builder.append(formatModuleImport(namespaceEntry.getKey()));
            }
            if (namespaceEntry.getValue().isEmpty()) {
                continue;
            }
            String namespaceImport = formatSingleLineImport(namespaceEntry.getKey(), namespaceEntry.getValue());
            if (namespaceImport.length() > CodegenUtils.MAX_PREFERRED_LINE_LENGTH) {
                namespaceImport = formatMultiLineImport(namespaceEntry.getKey(), namespaceEntry.getValue());
            }
            builder.append(namespaceImport);
        }
        builder.append("\n");
    }

    private String formatModuleImport(String namespace) {
        return String.format(MODULE_IMPORT_TEMPLATE, namespace);
    }

    private String formatSingleLineImport(String namespace, Map<String, String> names) {
        StringBuilder builder = new StringBuilder("from ").append(namespace).append(" import");
        for (Iterator<Map.Entry<String, String>> iter = names.entrySet().iterator(); iter.hasNext();) {
            Map.Entry<String, String> entry = iter.next();
            builder.append(" ").append(entry.getKey());
            if (!entry.getKey().equals(entry.getValue())) {
                builder.append(" as ").append(entry.getValue());
            }
            if (iter.hasNext()) {
                builder.append(",");
            }
        }
        builder.append("\n");
        return builder.toString();
    }

    private String formatMultiLineImport(String namespace, Map<String, String> names) {
        StringBuilder builder = new StringBuilder("from ").append(namespace).append(" import (\n");
        for (Map.Entry<String, String> entry : names.entrySet()) {
            builder.append("    ").append(entry.getKey());
            if (!entry.getKey().equals(entry.getValue())) {
                builder.append(" as ").append(entry.getValue());
            }
            builder.append(",\n");
        }
        builder.append(")\n");
        return builder.toString();
    }
}
