/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.InputParams;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.SyncVariant;
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
            writer.write("# Static type fixture: pyright over this validates models.pyi and the");
            writer.write("# client method signatures. Not executed as a test; it only needs to");
            writer.write("# type-check.\n");
            // Fills required members: Any is assignable to every field type, so the fixture
            // verifies the stub's constructor accepts each kwarg, not the value's type.
            writer.addStdlibImport("typing", "Any");
            writer.write("_: Any = ...\n");
            for (var shape : shapes) {
                if (shape instanceof StructureShape struct && !struct.hasTrait(ErrorTrait.class)) {
                    writeStructUsage(writer, struct, index, operationIndex, module);
                }
            }
            writeParamsUsage(writer, module);
            writeOperationCalls(writer);
        });
    }

    // Assigns a minimal dictionary to every dictionary form, so the type checker
    // verifies the stub declares each one and spells its required keys correctly.
    private void writeParamsUsage(PythonWriter writer, String module) {
        var inputParams = new InputParams(context);
        var count = 0;
        for (var shape : shapes) {
            // Union members have single-key forms too; the union's own form covers them.
            if (shape.isMemberShape() || !inputParams.hasParams(shape)) {
                continue;
            }
            var name = inputParams.paramsSymbol(shape).getName();
            writer.addImport(module + ".models", name);
            var keys = new StringBuilder();
            if (shape.isUnionShape()) {
                // Exactly one variant must be set; any one of them will do.
                var variant = shape.members().iterator().next();
                keys.append('"').append(symbolProvider.toMemberName(variant)).append("\": _");
            } else {
                appendRequired(keys, shape, inputParams, key -> "\"" + key + "\": _");
            }
            writer.write("_params_$L: $L = {$L}", count++, name, keys);
        }
    }

    // Calls every operation of both clients, with only its required members, with a
    // whole request unpacked from the input's dictionary form, and with a whole
    // request passed positionally as the input model or its dictionary form, so the
    // type checker verifies the generated method signatures against the stub.
    private void writeOperationCalls(PythonWriter writer) {
        var inputParams = new InputParams(context);
        var service = settings.service(model);
        var asyncClient = symbolProvider.toSymbol(service);
        var syncClient = SyncVariant.mapper(settings).apply(asyncClient);
        var eventStreamIndex = EventStreamIndex.of(model);
        var asyncCalls = new ArrayList<String>();
        var syncCalls = new ArrayList<String>();
        for (var operation : TopDownIndex.of(model).getContainedOperations(service)) {
            var method = symbolProvider.toSymbol(operation)
                    .expectProperty(SymbolProperties.OPERATION_METHOD)
                    .getName();
            var input = model.expectShape(operation.getInputShape());
            var arguments = new StringBuilder();
            appendRequired(arguments, input, inputParams, name -> name + "=_");
            var inputModel = symbolProvider.toSymbol(input);
            writer.addImport(inputModel.getNamespace(), inputModel.getName());
            var plainForm = inputParams.paramsSymbol(input);
            writer.addImport(plainForm.getNamespace(), plainForm.getName());
            var calls = new ArrayList<String>();
            calls.add(String.format("client.%s(%s)", method, arguments));
            // The plain dictionary form unpacks into either client, and either client
            // takes it, or the input model, as the whole request.
            calls.add(String.format("client.%s(**_request(%s))", method, plainForm.getName()));
            calls.add(String.format("client.%s(_request(%s))", method, inputModel.getName()));
            calls.add(String.format("client.%s(_request(%s))", method, plainForm.getName()));
            calls.forEach(call -> asyncCalls.add("await " + call));
            if (inputParams.hasAsyncParams(input)) {
                // Only the async client takes the form whose body may be an async stream.
                var asyncForm = inputParams.asyncParamsSymbol(input).getName();
                writer.addImport(settings.moduleName() + ".models", asyncForm);
                asyncCalls.add(String.format("await client.%s(**_request(%s))", method, asyncForm));
                asyncCalls.add(String.format("await client.%s(_request(%s))", method, asyncForm));
            }
            // Sync clients don't support event streams.
            if (eventStreamIndex.getInputInfo(operation).isEmpty()
                    && eventStreamIndex.getOutputInfo(operation).isEmpty()) {
                syncCalls.addAll(calls);
            }
        }
        writer.addImport(asyncClient.getNamespace(), asyncClient.getName());
        writer.addImport(syncClient.getNamespace(), syncClient.getName());
        writer.write("""

                def _request[T](form: type[T]) -> T:
                    raise NotImplementedError
                """);
        writer.openBlock("async def check_async_calls(client: $L) -> None:", "", asyncClient.getName(), () -> {
            writer.write("pass");
            asyncCalls.forEach(call -> writer.write("$L", call));
        });
        writer.openBlock("def check_sync_calls(client: $L) -> None:", "", syncClient.getName(), () -> {
            writer.write("pass");
            syncCalls.forEach(call -> writer.write("$L", call));
        });
    }

    private void appendRequired(
            StringBuilder out,
            Shape structure,
            InputParams inputParams,
            Function<String, String> format
    ) {
        for (var member : structure.members()) {
            if (inputParams.isParameter(member) && inputParams.mustBeSet(member)) {
                if (out.length() > 0) {
                    out.append(", ");
                }
                out.append(format.apply(symbolProvider.toMemberName(member)));
            }
        }
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
