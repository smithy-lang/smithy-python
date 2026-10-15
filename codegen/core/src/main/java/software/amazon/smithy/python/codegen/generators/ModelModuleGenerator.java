/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import software.amazon.smithy.model.loader.Prelude;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
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

            var symbolProvider = context.symbolProvider();
            // A shape whose generated symbol name differs from its shape-id name (a
            // conflict resolved by renaming, e.g. two GreetingStruct in different
            // namespaces) is unresolvable from the schema id name alone, which the
            // index collapses to one entry. Map such symbols directly to their unique
            // schema constant so build(symbol_name) finds the right schema.
            var renames = new LinkedHashMap<String, String>();
            // name -> schema-const for every model shape plus every union variant and
            // Unknown class, so the registry resolves build(name) without hydrating the
            // whole module just to construct this map.
            var index = new LinkedHashMap<String, String>();
            // every real shape-id name, so the registry reproduces the symbol provider's
            // variant-name collision disambiguation at build time.
            var shapeNames = new TreeSet<String>();

            for (var shape : shapes) {
                if (!isModelShape(shape) || Prelude.isPreludeShape(shape)) {
                    continue;
                }
                var symbol = symbolProvider.toSymbol(shape);
                var schemaRef = symbol.getProperty(SymbolProperties.SCHEMA);
                if (schemaRef.isEmpty()) {
                    continue;
                }
                var constName = schemaRef.get().getSymbol().getName();
                var symbolName = symbol.getName();
                var idName = shape.getId().getName();
                shapeNames.add(idName);
                index.put(idName, constName);
                if (!symbolName.equals(idName)) {
                    renames.put(symbolName, constName);
                }
                if (shape.isUnionShape()) {
                    for (var member : shape.asUnionShape().get().members()) {
                        index.put(symbolProvider.toSymbol(member).getName(), constName);
                    }
                    index.put(
                            symbol.expectProperty(SymbolProperties.UNION_UNKNOWN).getName(),
                            constName);
                }
            }

            writer.openBlock("_registry = ModelRegistry(", ")\n", () -> {
                writer.write("_schemas,");
                writeStringMap(writer, "renames", renames);
                writeStringMap(writer, "index", index);
                writer.openBlock("shape_names=frozenset({", "}),", () -> {
                    for (var name : shapeNames) {
                        writer.write("$S,", name);
                    }
                });
                // The runtime bases modeled errors on this service's ServiceError (not
                // ModeledError) so `except ServiceError` catches them, matching the eager
                // generator. ServiceErrorGenerator emits it into this same models module.
                writer.write("service_error=\"ServiceError\",");
            });

            // No runtime __all__: names are provided lazily by __getattr__ (a static
            // __all__ would trip F822). The typed __all__Lives in models.pyi.
            writer.write("""
                    def __getattr__(name: str):
                        return _registry.build(name)
                    """);
        });
    }

    private static void writeStringMap(PythonWriter writer, String keyword, Map<String, String> map) {
        if (map.isEmpty()) {
            writer.write("$L={},", keyword);
            return;
        }
        writer.openBlock(keyword + "={", "},", () -> {
            for (var entry : map.entrySet()) {
                writer.write("$S: $S,", entry.getKey(), entry.getValue());
            }
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
