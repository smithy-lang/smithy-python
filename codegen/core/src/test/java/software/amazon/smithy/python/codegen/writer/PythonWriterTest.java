/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;

public class PythonWriterTest {

    private PythonSettings createMockSettings() {
        PythonSettings settings = mock(PythonSettings.class);
        when(settings.moduleName()).thenReturn("testmodule");
        return settings;
    }

    private GenerationContext createMockContext(boolean isAwsService) {
        GenerationContext context = mock(GenerationContext.class);
        Model model = mock(Model.class);
        PythonSettings settings = createMockSettings();

        ShapeId serviceId = ShapeId.from("test.service#TestService");
        ServiceShape serviceShape = mock(ServiceShape.class);

        when(context.model()).thenReturn(model);
        when(context.settings()).thenReturn(settings);
        when(settings.service()).thenReturn(serviceId);
        when(model.expectShape(serviceId)).thenReturn(serviceShape);

        if (isAwsService) {
            when(serviceShape.hasTrait(software.amazon.smithy.aws.traits.ServiceTrait.class)).thenReturn(true);
        } else {
            when(serviceShape.hasTrait(software.amazon.smithy.aws.traits.ServiceTrait.class)).thenReturn(false);
        }

        return context;
    }

    @Test
    public void testWriteDocsShortStringOnSingleLine() {
        // Short documentation should be on a single line
        PythonWriter writer = new PythonWriter(createMockSettings(), "test.module", false);
        String shortDocs = "<p>This is a short documentation string.</p>";

        writer.writeDocs(shortDocs, createMockContext(true));
        String output = writer.toString();

        String expected = "\"\"\"This is a short documentation string.\"\"\"\n";
        assertEquals(expected, output);
    }

    @Test
    public void testWriteDocsVeryLongStringWrappedCorrectly() {
        // Very long documentation should be wrapped at 72 characters per line
        PythonWriter writer = new PythonWriter(createMockSettings(), "test.module", false);
        String veryLongDocs = "<p>This is an extremely long documentation string that definitely exceeds "
                + "the 72 character limit set by pandoc and should be wrapped to multiple lines "
                + "to ensure readability and proper formatting in the generated Python code.</p>";

        writer.writeDocs(veryLongDocs, createMockContext(true));
        String output = writer.toString();

        String expected = """
                ""\"This is an extremely long documentation string that definitely exceeds
                the 72 character limit set by pandoc and should be wrapped to multiple
                lines to ensure readability and proper formatting in the generated
                Python code.
                ""\"
                """;
        assertEquals(expected, output);
    }

    @Test
    public void testWriteDocsPreservesDollarSigns() {
        // Documentation with $ should be preserved in final output
        // (The intermediate format uses $$ for Smithy, but final output has $)
        PythonWriter writer = new PythonWriter(createMockSettings(), "test.module", false);
        String docsWithDollar = "<p>Use $variable in your code.</p>";

        writer.writeDocs(docsWithDollar, createMockContext(true));
        String output = writer.toString();

        String expected = "\"\"\"Use $variable in your code.\"\"\"\n";
        assertEquals(expected, output);
    }

}
