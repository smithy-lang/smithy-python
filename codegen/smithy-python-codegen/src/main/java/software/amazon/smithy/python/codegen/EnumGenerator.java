/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.util.Iterator;
import java.util.Locale;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumDefinition;
import software.amazon.smithy.model.traits.EnumTrait;

/**
 * Renders enums.
 */
final class EnumGenerator implements Runnable {
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final StringShape shape;

    EnumGenerator(Model model, SymbolProvider symbolProvider, PythonWriter writer, StringShape enumShape) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = enumShape;
    }

    @Override
    public void run() {
        var enumTrait = shape.expectTrait(EnumTrait.class);
        var enumSymbol = symbolProvider.toSymbol(shape).expectProperty("enumSymbol", Symbol.class);
        enumTrait.getEnumDefinitionValues();
        writer.openBlock("class $L:", "", enumSymbol.getName(), () -> {
            shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                writer.openDocComment(() -> writer.write(writer.formatDocs(trait.getValue())));
            });


            for (EnumDefinition definition : enumTrait.getValues()) {
                if (definition.getName().isPresent()) {
                    var name = definition.getName().get().toUpperCase(Locale.ENGLISH);
                    definition.getDocumentation().ifPresent(writer::writeComment);
                    writer.write("$L = $S\n", name, definition.getValue());
                }
            }

            writer.writeComment("""
                This set contains every possible value known at the time this was \
                generated. New values may be added in the future.""");
            writer.writeInline("values = frozenset(");
            for (Iterator<String> iter = enumTrait.getEnumDefinitionValues().iterator(); iter.hasNext();) {
                writer.writeInline("$S", iter.next());
                if (iter.hasNext()) {
                    writer.writeInline(", ");
                }
            }
            writer.writeInline(")\n");
        });
    }
}
