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
import software.amazon.smithy.model.shapes.MapShape;

/**
 * Generates private helper methods for maps.
 */
public class MapGenerator implements Runnable {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final MapShape shape;

    MapGenerator(
            Model model,
            SymbolProvider symbolProvider,
            PythonWriter writer,
            MapShape shape
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
        var target = model.expectShape(shape.getValue().getTarget());
        var targetSymbol = symbolProvider.toSymbol(target);

        writer.addStdlibImport("Any", "Any", "typing");
        writer.addStdlibImport("Dict", "Dict", "typing");
        writer.openBlock("def $L(given: $T) -> Dict[str, Any]:", "", asDictSymbol.getName(), symbol, () -> {
            if (target.isUnionShape() || target.isStructureShape()) {
                writer.write("return {k: v.as_dict() for k, v in given.items()}");
            } else if (target.isMapShape() || target instanceof CollectionShape) {
                var targetAsDictSymbol = targetSymbol.expectProperty("asDict", Symbol.class);
                writer.write("return {k, $T(v) for k, v in given.items()}", targetAsDictSymbol);
            }
        });
    }

    private void writeFromDict() {
        var symbol = symbolProvider.toSymbol(shape);
        var fromDictSymbol = symbol.expectProperty("fromDict", Symbol.class);
        var target = model.expectShape(shape.getValue().getTarget());
        var targetSymbol = symbolProvider.toSymbol(target);

        writer.addStdlibImport("Any", "Any", "typing");
        writer.addStdlibImport("Dict", "Dict", "typing");
        writer.openBlock("def $L(given: Dict[str, Any]) -> $T:", "", fromDictSymbol.getName(), symbol, () -> {
            if (target.isUnionShape() || target.isStructureShape()) {
                writer.write("return {k: $T.from_dict(v) for k, v in given.items()}");
            } else if (target.isMapShape() || target instanceof CollectionShape) {
                var targetFromDictSymbol = targetSymbol.expectProperty("fromDict", Symbol.class);
                writer.write("return {k, $T(v) for k, v in given.items()}", targetFromDictSymbol);
            }
        });
    }
}
