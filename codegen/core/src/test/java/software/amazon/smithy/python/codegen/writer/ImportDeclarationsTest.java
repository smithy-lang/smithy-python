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

    @Test
    public void testAliasImportRewritesTypeCheckingImports() {
        ImportDeclarations imports = createImports();
        imports.addTypeCheckingImport(MODULE + ".models", "Foo", "Foo");
        imports.addTypeCheckingImport("smithy_core.documents", "Document", "Document");

        imports.aliasImport(MODULE + ".models", "Foo", "_Foo");
        imports.aliasImport("smithy_core.documents", "Document", "_Document");

        String typeChecking = normalize(imports.toString().substring(imports.toString().indexOf("if TYPE_CHECKING:")));
        assertTrue(typeChecking.contains("from .models import Foo as _Foo"));
        assertTrue(typeChecking.contains("from smithy_core.documents import Document as _Document"));
    }

    @Test
    public void testRuntimeImportIsNotRepeatedUnderTypeChecking() {
        ImportDeclarations imports = createImports();
        imports.addImport(MODULE + ".models", "Foo", "Foo");
        imports.addStdlibImport("collections.abc", "Mapping");
        imports.addTypeCheckingImport(MODULE + ".models", "Foo", "Foo");
        imports.addTypeCheckingImport("collections.abc", "Mapping", "Mapping");
        imports.addTypeCheckingImport(MODULE + ".models", "Bar", "Bar");

        String out = imports.toString();
        String typeChecking = normalize(out.substring(out.indexOf("if TYPE_CHECKING:")));
        assertTrue(typeChecking.contains("from .models import Bar"));
        assertFalse(typeChecking.contains("Foo"));
        assertFalse(typeChecking.contains("Mapping"));
    }

    @Test
    public void testTypeCheckingBlockIsOmittedWhenEveryNameIsImportedAtRuntime() {
        ImportDeclarations imports = createImports();
        imports.addImport(MODULE + ".models", "Foo", "Foo");
        imports.addTypeCheckingImport(MODULE + ".models", "Foo", "Foo");

        assertFalse(imports.toString().contains("TYPE_CHECKING"));
    }

    @Test
    public void testTypeCheckingImportsListRelativeImportsLast() {
        ImportDeclarations imports = createImports();
        imports.addTypeCheckingImport(MODULE + ".models", "Foo", "Foo");
        imports.addTypeCheckingImport("collections.abc", "Sequence", "Sequence");

        String out = imports.toString();
        String typeChecking = out.substring(out.indexOf("if TYPE_CHECKING:"));
        assertTrue(
                typeChecking.indexOf("from collections.abc import Sequence") < typeChecking
                        .indexOf("from .models import Foo"),
                typeChecking);
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
