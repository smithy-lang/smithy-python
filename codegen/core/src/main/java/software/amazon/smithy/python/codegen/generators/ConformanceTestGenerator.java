/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.List;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.ParamsIndex;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits maintainer-only conformance tests into a generated client:
 *
 * <ul>
 *   <li>{@code tests/test_model_conformance.py} -- calls
 *       {@code smithy_test.verify_models} to assert every lazily-built model class
 *       matches its schema and the {@code models.pyi} stub, and the
 *       {@code _params.pyi} TypedDicts match the runtime's dictionary forms; and
 *       {@code smithy_test.verify_client} to assert each operation method takes the
 *       parameters the runtime accepts and matches {@code client.pyi}.
 *   <li>{@code tests/_typecheck.py} -- a usage fixture; running pyright over it
 *       validates the stubs' static types (the one layer runtime introspection cannot
 *       cover): each structure's constructor, the Params re-exports from
 *       {@code models}, and each operation's signature against its input TypedDict.
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
    private final ParamsIndex paramsIndex;
    private final List<Shape> shapes;

    public ConformanceTestGenerator(GenerationContext context, List<Shape> shapes) {
        this.context = context;
        this.settings = context.settings();
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.paramsIndex = ParamsIndex.of(context);
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

                    from smithy_test import verify_client, verify_models

                    from $1L import client as _client
                    from $1L import models as _models
                    from $1L._private import schemas as _schemas


                    def test_model_conformance() -> None:
                        pyi = Path(_models.__file__).with_suffix(".pyi")
                        params_pyi = Path(_models.__file__).with_name("_params.pyi")
                        verify_models(
                            _models,
                            _schemas,
                            pyi_path=str(pyi) if pyi.exists() else None,
                            params_pyi_path=str(params_pyi) if params_pyi.exists() else None,
                        )


                    def test_client_conformance() -> None:
                        verify_client(
                            _client.$2L,
                            {
                                ${3C|}
                            },
                            pyi_path=str(Path(_client.__file__).with_suffix(".pyi")),
                        )
                    """,
                    module,
                    symbolProvider.toSymbol(service()).getName(),
                    writer.consumer(this::writeOperationConstants));
        });
    }

    // Maps each operation method to the operation it invokes.
    private void writeOperationConstants(PythonWriter writer) {
        for (OperationShape operation : TopDownIndex.of(model).getContainedOperations(service())) {
            var symbol = symbolProvider.toSymbol(operation);
            writer.write("$S: _models.$L,",
                    symbol.expectProperty(SymbolProperties.OPERATION_METHOD).getName(),
                    symbol.getName());
        }
    }

    private ServiceShape service() {
        return settings.service(model);
    }

    private void writeTypecheckFixture() {
        var module = settings.moduleName();
        var filename = "tests/_typecheck.py";
        var index = NullableIndex.of(model);
        var operationIndex = OperationIndex.of(model);
        context.writerDelegator().useFileWriter(filename, "tests._typecheck", writer -> {
            writer.write("# Static type fixture: pyright over this validates models.pyi, _params.pyi,");
            writer.write("# and client.pyi. Not executed as a test; it only needs to type-check.\n");
            // Importing every Params form from models checks that models.pyi re-exports it.
            writer.writeReexports(module + ".models", paramsIndex.getNames());
            // Fills required members: Any is assignable to every field type, so the fixture
            // verifies the stub's constructor accepts each kwarg, not the value's type.
            writer.addStdlibImport("typing", "Any");
            writer.write("_: Any = ...\n");
            for (var shape : shapes) {
                if (shape instanceof StructureShape struct && !struct.hasTrait(ErrorTrait.class)) {
                    writeStructUsage(writer, struct, index, operationIndex, module);
                }
            }
            var clientSymbol = symbolProvider.toSymbol(service());
            writer.addImport(clientSymbol.getNamespace(), clientSymbol.getName());
            for (OperationShape operation : TopDownIndex.of(model).getContainedOperations(service())) {
                writeOperationUsage(writer, operation, clientSymbol.getName());
            }
        });
    }

    // Unpacking the input's Params form, with only its required keys, into the method
    // makes pyright check the TypedDict and the method's parameters against each other.
    // The function is public so that strict pyright doesn't report it as unused.
    private void writeOperationUsage(PythonWriter writer, OperationShape operation, String clientName) {
        var method = symbolProvider.toSymbol(operation).expectProperty(SymbolProperties.OPERATION_METHOD).getName();
        var input = model.expectShape(operation.getInputShape(), StructureShape.class);
        var keys = new ArrayList<String>();
        for (MemberShape member : paramsIndex.getMembers(input)) {
            if (CodegenUtils.isRequiredParameter(model, member)) {
                keys.add(String.format("\"%s\": _", symbolProvider.toMemberName(member)));
            }
        }
        writer.write("""

                async def check_$1L(client: $2L) -> None:
                    params: $3L = {$4L}
                    await client.$1L(**params)
                """, method, clientName, paramsIndex.getParamsSymbol(input).getName(), String.join(", ", keys));
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
                        && !CodegenUtils.isErrorMessage(model, member)
                        && !CodegenUtils.isEventStreamMember(model, member)) {
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
