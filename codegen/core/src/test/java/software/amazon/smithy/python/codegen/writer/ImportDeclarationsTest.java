/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.python.codegen.PythonSettings;

public class ImportDeclarationsTest {

    private static final String MODULE = "aws_sdk_example";
    private static final String LOCAL_NAMESPACE = MODULE + ".config";

    @Test
    public void testAliasImportRewritesStdlibImport() {
        ImportDeclarations imports = createImports();
        imports.addStdlibImport("decimal", "Decimal");

        imports.aliasImport("decimal", "Decimal", "_Decimal");

        String out = imports.toString();
        assertTrue(normalize(out).contains("from decimal import Decimal as _Decimal"));
    }

    @Test
    public void testAliasImportRewritesExternalImport() {
        ImportDeclarations imports = createImports();
        imports.addImport("smithy_core.documents", "Document", "Document");

        imports.aliasImport("smithy_core.documents", "Document", "_Document");

        String out = imports.toString();
        assertTrue(normalize(out).contains("from smithy_core.documents import Document as _Document"));
    }

    @Test
    public void testAliasImportRewritesLocalImport() {
        ImportDeclarations imports = createImports();
        imports.addImport(MODULE + ".models", "Foo", "Foo");

        imports.aliasImport(MODULE + ".models", "Foo", "_Foo");

        String out = imports.toString();
        assertTrue(normalize(out).contains("from .models import Foo as _Foo"));
    }

    @Test
    public void testAliasImportDoesNotOverwritePreExistingAlias() {
        ImportDeclarations imports = createImports();
        imports.addImport("smithy_core.documents", "Document", "OriginalAlias");

        imports.aliasImport("smithy_core.documents", "Document", "_ShouldNotApply");

        String out = imports.toString();
        String normalized = normalize(out);
        assertTrue(normalized.contains("from smithy_core.documents import Document as OriginalAlias"));
        assertFalse(normalized.contains("_ShouldNotApply"));
    }

    private static ImportDeclarations createImports() {
        PythonSettings settings = mock(PythonSettings.class);
        when(settings.moduleName()).thenReturn(MODULE);
        return new ImportDeclarations(settings, LOCAL_NAMESPACE);
    }

    /**
     * Collapses multi-line import blocks emitted by
     * {@link ImportDeclarations#formatMultiLineImport} into a single-line form so
     * {@code contains()} assertions stay stable regardless of whether the rendered
     * import exceeded {@code MAX_PREFERRED_LINE_LENGTH}.
     */
    private static String normalize(String output) {
        return output.replaceAll("\\(\\s+", "")
                .replaceAll(",\\s*\\)", "")
                .replaceAll("\\s+", " ");
    }
}
