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
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.PythonSettings;

public class PythonWriterTest {

    private static final String CURRENT_PACKAGE = "aws_sdk_example.models";

    @Test
    public void testFrameworkSymbolCollidingWithLocalIsAliased() {
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        Symbol framework = frameworkSymbol("smithy_core.documents", "Document");
        Symbol local = generatedSymbol(CURRENT_PACKAGE, "Document");
        writer.addLocallyDefinedSymbol(local);

        writer.write("value: $T", framework);
        String out = writer.toString();

        assertTrue(normalize(out).contains("from smithy_core.documents import Document as _Document"));
        assertTrue(out.contains("value: _Document"));
    }

    @Test
    public void testTwoFrameworkSymbolsWithSameSimpleNameGetModuleAliases() {
        PythonWriter writer = createWriter("aws_sdk_example.auth");
        Symbol a = frameworkSymbol("smithy_core.auth", "AuthOption");
        Symbol b = frameworkSymbol("smithy_core.interfaces.auth", "AuthOption");

        writer.write("x: $T", a);
        writer.write("y: $T", b);
        String out = writer.toString();
        String normalized = normalize(out);

        assertTrue(normalized.contains(
                "from smithy_core.auth import AuthOption as _smithy_core_auth_AuthOption"));
        assertTrue(normalized.contains(
                "from smithy_core.interfaces.auth import "
                        + "AuthOption as _smithy_core_interfaces_auth_AuthOption"));
        assertTrue(out.contains("x: _smithy_core_auth_AuthOption"));
        assertTrue(out.contains("y: _smithy_core_interfaces_auth_AuthOption"));
    }

    @Test
    public void testCrossFileGeneratedSymbolCollidingWithFrameworkImportIsAliased() {
        PythonWriter writer = createWriter("aws_sdk_example.config");
        Symbol framework = frameworkSymbol("smithy_core.aio.interfaces", "EndpointResolver");
        Symbol crossFileGenerated = generatedSymbol("aws_sdk_example.models", "EndpointResolver");

        writer.write("x: $T", framework);
        writer.write("y: $T", crossFileGenerated);
        String out = writer.toString();
        String normalized = normalize(out);

        assertTrue(normalized.contains(
                "from smithy_core.aio.interfaces import "
                        + "EndpointResolver as _smithy_core_aio_interfaces_EndpointResolver"));
        assertTrue(normalized.contains(
                "from .models import EndpointResolver as _aws_sdk_example_models_EndpointResolver"));
    }

    @Test
    public void testSymbolDefinedInCurrentWriterFileIsNotRegistered() {
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        Symbol selfReference = generatedSymbol(CURRENT_PACKAGE, "MyStruct");
        writer.addLocallyDefinedSymbol(selfReference);

        writer.write("value: $T", selfReference);
        String out = writer.toString();

        assertFalse(out.contains("import MyStruct"));
        assertFalse(out.contains("_MyStruct"));
        assertTrue(out.contains("value: MyStruct"));
    }

    @Test
    public void testSymbolReferencedByCompositeCollidingWithFrameworkImportIsAliased() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        Symbol framework = frameworkSymbol("smithy_core.documents", "Document");
        Symbol crossFileGenerated = generatedSymbol("aws_sdk_example.models", "Document");

        writer.write("x: $T", framework);
        writer.write("y: $T", listOf(crossFileGenerated));
        writer.write("z: $T", listOf(listOf(crossFileGenerated)));
        String out = writer.toString();
        String normalized = normalize(out);

        assertTrue(normalized.contains(
                "from smithy_core.documents import Document as _smithy_core_documents_Document"));
        assertTrue(normalized.contains(
                "from .models import Document as _aws_sdk_example_models_Document"));
        assertTrue(out.contains("x: _smithy_core_documents_Document"));
        assertTrue(out.contains("y: list[_aws_sdk_example_models_Document]"));
        assertTrue(out.contains("z: list[list[_aws_sdk_example_models_Document]]"));
    }

    @Test
    public void testCompositeAliasRewritesOnlyWholeNames() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        Symbol framework = frameworkSymbol("smithy_core.documents", "Document");
        Symbol colliding = generatedSymbol("aws_sdk_example.models", "Document");
        Symbol similar = generatedSymbol("aws_sdk_example.models", "DocumentList");
        Symbol composite = Symbol.builder()
                .name("dict[DocumentList, Document]")
                .addReference(similar)
                .addReference(colliding)
                .build();

        writer.write("x: $T", framework);
        writer.write("y: $T", composite);
        String out = writer.toString();

        assertTrue(out.contains("y: dict[DocumentList, _aws_sdk_example_models_Document]"));
    }

    @Test
    public void testCompositeWithoutCollisionKeepsPlainNames() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        Symbol crossFileGenerated = generatedSymbol("aws_sdk_example.models", "Document");

        writer.write("y: $T", listOf(crossFileGenerated));
        String out = writer.toString();

        assertTrue(normalize(out).contains("from .models import Document"));
        assertTrue(out.contains("y: list[Document]"));
    }

    private static Symbol listOf(Symbol member) {
        return Symbol.builder().name("list[" + member.getName() + "]").addReference(member).build();
    }

    private static PythonWriter createWriter(String fullPackageName) {
        PythonSettings settings = mock(PythonSettings.class);
        when(settings.moduleName()).thenReturn(fullPackageName.split("\\.")[0]);
        return new PythonWriter(settings, fullPackageName);
    }

    private static Symbol frameworkSymbol(String namespace, String name) {
        return Symbol.builder().name(name).namespace(namespace, ".").build();
    }

    private static Symbol generatedSymbol(String namespace, String name) {
        return Symbol.builder()
                .name(name)
                .namespace(namespace, ".")
                .definitionFile("./src/" + namespace.replace('.', '/') + ".py")
                .build();
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
