/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.List;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits the runtime {@code models.py}: a thin module that builds model classes on
 * demand from the compact schemas via {@link smithy_core._dynamic_models.ModelRegistry},
 * instead of eager per-shape dataclasses. The typed surface for static tooling is
 * emitted separately as {@code models.pyi}.
 */
@SmithyInternalApi
public final class ModelModuleGenerator implements Runnable {

    private final GenerationContext context;
    private final PythonSettings settings;
    private final List<Shape> shapes;

    public ModelModuleGenerator(GenerationContext context, List<Shape> shapes) {
        this.context = context;
        this.settings = context.settings();
        this.shapes = shapes;
    }

    @Override
    public void run() {
        var module = settings.moduleName();
        var filename = String.format("src/%s/models.py", module);
        var namespace = String.format("%s.models", module);

        context.writerDelegator().useFileWriter(filename, namespace, writer -> {
            // addImport hoists these into the file's import block so they land at the
            // top even though ServiceError/operations also write into this file.
            writer.addImport("smithy_core._dynamic_models", "ModelRegistry");
            writer.addImport("._private", "schemas", "_schemas");
            // A shape whose generated symbol name differs from its shape-id name (a
            // conflict resolved by renaming, e.g. two GreetingStruct in different
            // namespaces) is unresolvable from the schema id name alone, which the
            // registry's index collapses to one entry. Map such symbols directly to
            // their unique schema constant so build(symbol_name) finds the right schema.
            var symbolProvider = context.symbolProvider();
            var renames = new java.util.LinkedHashMap<String, String>();
            for (var shape : shapes) {
                if (!isModelShape(shape)) {
                    continue;
                }
                var symbol = symbolProvider.toSymbol(shape);
                var symbolName = symbol.getName();
                var idName = shape.getId().getName();
                if (!symbolName.equals(idName)) {
                    var schemaRef = symbol.getProperty(software.amazon.smithy.python.codegen.SymbolProperties.SCHEMA);
                    if (schemaRef.isPresent()) {
                        renames.put(symbolName, schemaRef.get().getSymbol().getName());
                    }
                }
            }
            if (renames.isEmpty()) {
                writer.write("_registry = ModelRegistry(_schemas)\n");
            } else {
                writer.openBlock("_registry = ModelRegistry(_schemas, renames={", "})\n", () -> {
                    for (var entry : renames.entrySet()) {
                        writer.write("$S: $S,", entry.getKey(), entry.getValue());
                    }
                });
            }
            // No runtime __all__: names are provided lazily by __getattr__ (a static
            // __all__ would trip F822). The typed __all__Lives in models.pyi.
            writer.write("""
                    def __getattr__(name: str):
                        return _registry.build(name)
                    """);
        });
    }

    private boolean isModelShape(Shape shape) {
        var t = shape.getType();
        return t == ShapeType.STRUCTURE
                || t == ShapeType.UNION
                || t == ShapeType.ENUM
                || t == ShapeType.INT_ENUM;
    }
}
