/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

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

    private final Map<String, Map<String, String>> stdlibImports = new TreeMap<>();
    private final Map<String, Map<String, String>> externalImports = new TreeMap<>();
    private final Map<String, Map<String, String>> localImports = new TreeMap<>();

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

    public ImportDeclarations addImport(String namespace, String name, String alias) {
        var isTestModule = this.localNamespace.startsWith("tests");
        if (namespace.startsWith(settings.moduleName())) {
            // if the module is for tests, we shouldn't relativize the imports
            //  as python will complain that the imports are beyond the top-level package
            var ns = isTestModule ? namespace : relativize(namespace);
            return addImportToMap(ns, name, alias, localImports);
        }
        return addImportToMap(namespace, name, alias, externalImports);
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

    @Override
    public String toString() {
        if (externalImports.isEmpty() && stdlibImports.isEmpty() && localImports.isEmpty()) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        if (!stdlibImports.isEmpty()) {
            formatImportList(builder, stdlibImports);
        }
        if (!externalImports.isEmpty()) {
            formatImportList(builder, externalImports);
        }
        if (!localImports.isEmpty()) {
            formatImportList(builder, localImports);
        }
        builder.append("\n");
        return builder.toString();
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
