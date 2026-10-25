/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.GenerationContext;
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
    public void testTypeCheckingSymbolIsImportedOnlyUnderTypeChecking() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        writer.write("value: $A", generatedSymbol("aws_sdk_example.models", "MyStruct"));
        String out = writer.toString();

        assertTrue(out.contains("from __future__ import annotations"));
        assertFalse(beforeTypeChecking(out).contains("MyStruct"));
        assertTrue(normalize(afterTypeChecking(out)).contains("from .models import MyStruct"));
        assertTrue(out.contains("value: MyStruct"));
    }

    @Test
    public void testTypeCheckingSymbolCollidingWithLocalIsAliased() {
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        writer.addLocallyDefinedSymbol(generatedSymbol(CURRENT_PACKAGE, "Document"));

        writer.write("value: $A", frameworkSymbol("smithy_core.documents", "Document"));
        String out = writer.toString();

        assertTrue(normalize(afterTypeChecking(out))
                .contains("from smithy_core.documents import Document as _Document"));
        assertTrue(out.contains("value: _Document"));
    }

    @Test
    public void testSymbolImportedAtRuntimeIsNotRepeatedUnderTypeChecking() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        Symbol symbol = generatedSymbol("aws_sdk_example.models", "MyStruct");

        writer.write("value: $A = $T()", symbol, symbol);
        String out = writer.toString();

        assertTrue(normalize(out).contains("from .models import MyStruct"));
        assertFalse(out.contains("TYPE_CHECKING"));
    }

    @Test
    public void testTypeCheckingSymbolReferencesAreImportedUnderTypeChecking() {
        PythonWriter writer = createWriter("aws_sdk_example.client");
        Symbol jsonString = frameworkSymbol("smithy_core.types", "JsonString");
        Symbol union = Symbol.builder().name("str | JsonString").addReference(jsonString).build();

        writer.write("value: $A", union);
        String out = writer.toString();

        assertTrue(normalize(afterTypeChecking(out)).contains("from smithy_core.types import JsonString"));
        assertFalse(beforeTypeChecking(out).contains("JsonString"));
        assertTrue(out.contains("value: str | JsonString"));
    }

    @Test
    public void testBuiltinTypeCheckingSymbolIsNotImported() {
        PythonWriter writer = createWriter("aws_sdk_example.client");

        writer.write("value: $A", Symbol.builder().name("str").build());
        String out = writer.toString();

        assertFalse(out.contains("TYPE_CHECKING"));
        assertTrue(out.contains("value: str"));
    }

    @Test
    public void testLocallyDefinedNameAliasesImport() {
        // A parameter named like an imported function shadows it in the body.
        PythonWriter writer = createWriter("aws_sdk_example.client");
        writer.addLocallyDefinedName("user_agent_plugin");

        writer.write("plugins = [$T]", frameworkSymbol("smithy_http.plugins", "user_agent_plugin"));
        String out = writer.toString();

        assertTrue(normalize(out).contains("from smithy_http.plugins import user_agent_plugin as _user_agent_plugin"));
        assertTrue(out.contains("plugins = [_user_agent_plugin]"));
    }

    @Test
    public void testWriteReexportsKeepsRedundantAliases() {
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        writer.writeReexports("._params", List.of("AParams", "BParams"));
        String out = writer.toString();

        assertTrue(out.contains("from ._params import (\n    AParams as AParams,\n    BParams as BParams,\n)"), out);
    }

    @Test
    public void testWriteReexportsWritesNothingWithoutNames() {
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        writer.writeReexports("._params", List.of());

        assertFalse(writer.toString().contains("import"));
    }

    @Test
    public void testWriteDocsKeepsTripleQuotesInsideDocstring() {
        // S3 documents QuoteEscapeCharacter with the example """ a , b """, which
        // must not close the generated docstring early.
        PythonWriter writer = createWriter(CURRENT_PACKAGE);
        writer.writeDocs("<p>The value <code>\"\"\" a , b \"\"\"</code> is parsed.</p>", createAwsContext());
        String out = writer.toString();

        assertEquals("\"\"\"The value `\\\"\\\"\\\" a , b \\\"\\\"\\\"` is parsed.\"\"\"",
                out.substring(out.indexOf("\"\"\"")).trim());
    }

    private static GenerationContext createAwsContext() {
        GenerationContext context = mock(GenerationContext.class);
        Model model = mock(Model.class);
        PythonSettings settings = mock(PythonSettings.class);
        ShapeId serviceId = ShapeId.from("test.service#TestService");
        ServiceShape serviceShape = mock(ServiceShape.class);

        when(context.model()).thenReturn(model);
        when(context.settings()).thenReturn(settings);
        when(settings.service()).thenReturn(serviceId);
        when(model.expectShape(serviceId)).thenReturn(serviceShape);
        when(serviceShape.hasTrait(ServiceTrait.class)).thenReturn(true);
        return context;
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

    // The runtime imports all come before the TYPE_CHECKING block.
    private static String beforeTypeChecking(String output) {
        var index = output.indexOf("if TYPE_CHECKING:");
        return index < 0 ? output : output.substring(0, index);
    }

    private static String afterTypeChecking(String output) {
        var index = output.indexOf("if TYPE_CHECKING:");
        assertTrue(index >= 0, "missing TYPE_CHECKING block in:\n" + output);
        return output.substring(index);
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
