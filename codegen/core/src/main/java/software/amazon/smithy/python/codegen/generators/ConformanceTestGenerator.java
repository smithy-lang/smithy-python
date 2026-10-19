/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.List;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits maintainer-only conformance tests into a generated client:
 *
 * <ul>
 *   <li>{@code tests/test_model_conformance.py} -- calls
 *       {@code smithy_test.verify_models} to assert every lazily-built model class
 *       matches its schema and the {@code models.pyi} stub at runtime.
 *   <li>{@code tests/_typecheck.py} -- a per-shape usage fixture; running pyright over
 *       it validates the stub's static types (the one layer runtime introspection
 *       cannot cover).
 * </ul>
 *
 * These import {@code smithy_test}, a maintainer/test package customers do not depend
 * on, so a shipped client carries no test weight.
 */
@SmithyInternalApi
public final class ConformanceTestGenerator implements Runnable {

    private final GenerationContext context;
    private final PythonSettings settings;
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final List<Shape> shapes;

    public ConformanceTestGenerator(GenerationContext context, List<Shape> shapes) {
        this.context = context;
        this.settings = context.settings();
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.shapes = shapes;
    }

    @Override
    public void run() {
        writeConformanceTest();
        writeTypecheckFixture();
    }

    private void writeConformanceTest() {
        var module = settings.moduleName();
        var filename = String.format("tests/test_model_conformance.py", module);
        context.writerDelegator().useFileWriter(filename, "tests.test_model_conformance", writer -> {
            // Register the test deps the raw-string imports below rely on, so the
            // generated pyproject's test group installs them (CI's `uv pip install
            // --group test` fails to import smithy_test otherwise).
            writer.addDependency(SmithyPythonDependency.SMITHY_TEST);
            writer.addDependency(SmithyPythonDependency.PYTEST);
            writer.write("""
                    from pathlib import Path

                    from smithy_test import verify_models

                    from $1L import models as _models
                    from $1L._private import schemas as _schemas


                    def test_model_conformance() -> None:
                        pyi = Path(_models.__file__).with_suffix(".pyi")
                        verify_models(
                            _models,
                            _schemas,
                            pyi_path=str(pyi) if pyi.exists() else None,
                        )
                    """, module);
        });
    }

    private void writeTypecheckFixture() {
        var module = settings.moduleName();
        var filename = "tests/_typecheck.py";
        var index = NullableIndex.of(model);
        var operationIndex = OperationIndex.of(model);
        context.writerDelegator().useFileWriter(filename, "tests._typecheck", writer -> {
            writer.write("# Static type fixture: pyright over this validates models.pyi.");
            writer.write("# Not executed as a test; it only needs to type-check.\n");
            // Fills required members: Any is assignable to every field type, so the fixture
            // verifies the stub's constructor accepts each kwarg, not the value's type.
            writer.addStdlibImport("typing", "Any");
            writer.write("_: Any = ...\n");
            for (var shape : shapes) {
                if (shape instanceof StructureShape struct && !struct.hasTrait(ErrorTrait.class)) {
                    writeStructUsage(writer, struct, index, operationIndex, module);
                }
            }
        });
    }

    private void writeStructUsage(
            PythonWriter writer,
            StructureShape shape,
            NullableIndex index,
            OperationIndex operationIndex,
            String module
    ) {
        var name = symbolProvider.toSymbol(shape).getName();
        writer.addImport(module + ".models", name);
        // Construct with required (non-input) members so the type checker verifies the
        // constructor signature the stub declares.
        var args = new StringBuilder();
        if (!operationIndex.isInputStructure(shape)) {
            for (var member : shape.members()) {
                if (CodegenUtils.isRequiredMember(index, member)
                        && !CodegenUtils.isErrorMessage(model, member)) {
                    var memberName = symbolProvider.toMemberName(member);
                    if (args.length() > 0) {
                        args.append(", ");
                    }
                    args.append(memberName).append("=_");
                }
            }
        }
        writer.write("$1L($2L)", name, args.toString());
    }
}
