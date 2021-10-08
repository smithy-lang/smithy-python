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

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.CollectionShape;

/**
 * Generates private helper methods for collections.
 */
final class CollectionGenerator implements Runnable {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final CollectionShape shape;

    CollectionGenerator(
            Model model,
            SymbolProvider symbolProvider,
            PythonWriter writer,
            CollectionShape shape
    ) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = shape;
    }

    @Override
    public void run() {
        var symbol = symbolProvider.toSymbol(shape);
        if (symbol.getProperty("asDict").isPresent()) {
            writeAsDict();
        }
        if (symbol.getProperty("fromDict").isPresent()) {
            writeFromDict();
        }
    }

    private void writeAsDict() {
        var symbol = symbolProvider.toSymbol(shape);
        var asDictSymbol = symbol.expectProperty("asDict", Symbol.class);
        var target = model.expectShape(shape.getMember().getTarget());
        var targetSymbol = symbolProvider.toSymbol(target);
        writer.addStdlibImport("List", "List", "typing");
        writer.addStdlibImport("Any", "Any", "typing");
        writer.openBlock("def $L(given: $T) -> List[Any]:", "", asDictSymbol.getName(), symbol, () -> {
            if (target.isUnionShape() || target.isStructureShape()) {
                writer.write("return [v.as_dict() for v in given]");
            } else if (target.isMapShape() || target instanceof CollectionShape) {
                var targetAsDictSymbol = targetSymbol.expectProperty("asDict", Symbol.class);
                writer.write("return [$T(v) for v in given]", targetAsDictSymbol);
            } else {
                writer.write("return given");
            }
        });
    }

    private void writeFromDict() {
        var symbol = symbolProvider.toSymbol(shape);
        var fromDictSymbol = symbol.expectProperty("fromDict", Symbol.class);
        var target = model.expectShape(shape.getMember().getTarget());
        var targetSymbol = symbolProvider.toSymbol(target);
        writer.addStdlibImport("List", "List", "typing");
        writer.addStdlibImport("Any", "Any", "typing");
        writer.openBlock("def $L(given: List[Any]) -> $T:", "", fromDictSymbol.getName(), symbol, () -> {
            if (target.isUnionShape() || target.isStructureShape()) {
                writer.write("return [$T.from_dict(v) for v in given]", targetSymbol);
            } else if (target.isMapShape() || target instanceof CollectionShape) {
                var targetFromDictSymbol = targetSymbol.expectProperty("fromDict", Symbol.class);
                writer.write("return [$T(v) for v in given]", targetFromDictSymbol);
            } else {
                writer.write("return given");
            }
        });
    }
}
