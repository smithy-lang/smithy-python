/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.ParamTypeRenderer;
import software.amazon.smithy.python.codegen.ParamTypeRenderer.Parameter;
import software.amazon.smithy.python.codegen.ParamsIndex;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits {@code _params.pyi}: the {@code Params} TypedDicts that operation parameters
 * accept in place of models, for every shape in {@link ParamsIndex}.
 *
 * <p>They live in their own stub because pyright limits how complex one file may be,
 * and the largest services' {@code models.pyi} is already close to it. {@code models.pyi}
 * re-exports them. They have no docstrings, since the field docs are on the models.
 */
@SmithyInternalApi
public final class ParamsGenerator implements Runnable {

    private final GenerationContext context;
    private final SymbolProvider symbolProvider;
    private final ParamsIndex paramsIndex;
    private final ParamTypeRenderer typeRenderer;

    public ParamsGenerator(GenerationContext context) {
        this.context = context;
        this.symbolProvider = context.symbolProvider();
        this.paramsIndex = ParamsIndex.of(context);
        this.typeRenderer = new ParamTypeRenderer(context);
    }

    @Override
    public void run() {
        var module = context.settings().moduleName();
        var namespace = module + "._params";
        context.writerDelegator().useFileWriter(String.format("src/%s/_params.pyi", module), namespace, writer -> {
            for (Shape shape : paramsIndex.getShapes()) {
                if (shape instanceof StructureShape struct) {
                    writeStructure(writer, struct);
                } else if (shape instanceof UnionShape union) {
                    writeUnion(writer, union);
                }
            }
        });
        // The runtime module keeps pyright from reporting the stub as missing its
        // source, and resolves the names like models does, so an import from
        // _params (e.g. an editor's auto-import) also works at runtime.
        context.writerDelegator().useFileWriter(String.format("src/%s/_params.py", module), namespace, writer -> {
            writer.addStdlibImport("typing", "Any");
            writer.addImport(module, "models");
            writer.write("""
                    # The Params TypedDicts are declared in _params.pyi; at runtime each is a dict.


                    def __getattr__(name: str) -> type[dict[str, Any]]:
                        if getattr(models, name, None) is dict:
                            return dict
                        raise AttributeError(name)
                    """);
        });
    }

    private void writeStructure(PythonWriter writer, StructureShape shape) {
        var symbol = paramsIndex.getParamsSymbol(shape);
        writer.addLocallyDefinedSymbol(symbol);
        var parameters = typeRenderer.parameters(writer, shape, false);
        if (parameters.isEmpty()) {
            writer.write("class $L($T):\n    pass\n", symbol.getName(), RuntimeTypes.TYPED_DICT);
            return;
        }
        writer.openBlock("class $L($T, total=False):", "", symbol.getName(), RuntimeTypes.TYPED_DICT, () -> {
            for (Parameter parameter : parameters) {
                if (parameter.required()) {
                    writer.write("$L: $T[$L]", parameter.name(), RuntimeTypes.REQUIRED, parameter.type());
                } else {
                    writer.write("$L: $L | None", parameter.name(), parameter.type());
                }
            }
        });
        writer.write("");
    }

    private void writeUnion(PythonWriter writer, UnionShape shape) {
        var variants = new ArrayList<String>();
        for (MemberShape member : shape.members()) {
            var symbol = paramsIndex.getVariantParamsSymbol(member);
            writer.addLocallyDefinedSymbol(symbol);
            variants.add(symbol.getName());
            writer.openBlock("class $L($T):", "", symbol.getName(), RuntimeTypes.TYPED_DICT, () -> {
                writer.write("$L: $L",
                        symbolProvider.toMemberName(member),
                        typeRenderer.render(writer, member, false));
            });
            writer.write("");
        }
        var symbol = paramsIndex.getParamsSymbol(shape);
        writer.addLocallyDefinedSymbol(symbol);
        writer.write("$L = $L\n", symbol.getName(), String.join(" | ", variants));
    }
}
