/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen.integration;

import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;
import software.amazon.smithy.aws.traits.protocols.RestJson1Trait;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.knowledge.HttpBinding.Location;
import software.amazon.smithy.model.knowledge.HttpBindingIndex;
import software.amazon.smithy.model.knowledge.NeighborProviderIndex;
import software.amazon.smithy.model.neighbor.Walker;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestCase;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Abstract implementation of JSON-based protocols that use REST bindings.
 *
 * <p>This class will be capable of generating a functional protocol based on
 * the semantics of Amazon's RestJson1 protocol. Extension hooks will be
 * provided where necessary in the few cases where that protocol uses
 * Amazon-specific terminology or functionality.
 */
@SmithyUnstableApi
public class RestJsonProtocolGenerator extends HttpBindingProtocolGenerator {

    private static final Set<String> TESTS_TO_SKIP = Set.of(
        // These two tests essentially try to assert nan == nan,
        // which is never true. We should update the generator to
        // make specific assertions for these.
        "RestJsonSupportsNaNFloatHeaderOutputs",
        "RestJsonSupportsNaNFloatInputs",

        // This requires support of idempotency autofill
        "RestJsonQueryIdempotencyTokenAutoFill",

        // This requires support of the httpChecksumRequired trait
        "RestJsonHttpChecksumRequired",

        // These require support of the endpoint trait
        "RestJsonEndpointTraitWithHostLabel",
        "RestJsonEndpointTrait"
    );

    @Override
    public ShapeId getProtocol() {
        return RestJson1Trait.ID;
    }

    @Override
    protected Format getDocumentTimestampFormat() {
        return Format.EPOCH_SECONDS;
    }

    @Override
    protected String getDocumentContentType() {
        return "application/json";
    }

    // This is here rather than in HttpBindingProtocolGenerator because eventually
    // it will need to generate some protocol-specific comparators.
    @Override
    public void generateProtocolTests(GenerationContext context) {
        context.writerDelegator().useFileWriter("./tests/test_protocol.py", "tests.test_protocol", writer -> {
            new HttpProtocolTestGenerator(
                context, getProtocol(), writer, (shape, testCase) -> filterTests(context, shape, testCase)
            ).run();
        });
    }

    private boolean filterTests(GenerationContext context, Shape shape, HttpMessageTestCase testCase) {
        if (TESTS_TO_SKIP.contains(testCase.getId())) {
            return true;
        }
        var bindingIndex = HttpBindingIndex.of(context.model());
        if (testCase instanceof HttpRequestTestCase) {
            return bindingIndex.getRequestBindings(shape, Location.PAYLOAD).size() != 0;
        } else {
            return bindingIndex.getResponseBindings(shape, Location.PAYLOAD).size() != 0;
        }
    }

    @Override
    protected void serializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.write("result: dict[str, Document] = {}\n");

        var bodyMembers = documentBindings.stream()
            .map(HttpBinding::getMember)
            .collect(Collectors.toSet());

        var serVisitor = new JsonShapeSerVisitor(context, writer);
        serVisitor.structureMembers(bodyMembers);

        writer.addStdlibImport("json", "dumps", "json_dumps");
        writer.write("body = json_dumps(result).encode('utf-8')");
    }

    @Override
    protected void generateDocumentBodyShapeSerializers(GenerationContext context, Set<Shape> shapes) {
        for (Shape shape : getConnectedShapes(context, shapes)) {
            var serFunction = context.protocolGenerator().getSerializationFunction(context, shape);
            context.writerDelegator().useFileWriter(serFunction.getDefinitionFile(),
                serFunction.getNamespace(), writer -> {
                    shape.accept(new JsonShapeSerVisitor(context, writer));
                });
        }
    }

    @Override
    protected void deserializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.types", "Document");
        writer.addStdlibImport("json", "loads", "json_loads");

        if (operationOrError.isOperationShape()) {
            writer.write("""
                output: dict[str, Document] = {}
                if (body := await http_response.consume_body()):
                    output = json_loads(body)

                """);
        } else {
            // The method that parses the error code will also pre-parse the body.
            // The only time it doesn't is for streaming payloads, which isn't
            // relevant here.
            writer.addStdlibImport("typing", "cast");
            writer.write("""
                output: dict[str, Document] = cast(dict[str, Document], parsed_body)

                """);
        }

        var bodyMembers = documentBindings.stream()
            .map(HttpBinding::getMember)
            .collect(Collectors.toSet());

        var deserVisitor = new JsonShapeDeserVisitor(context, writer);
        deserVisitor.structureMembers(bodyMembers);
    }

    @Override
    protected void generateDocumentBodyShapeDeserializers(
        GenerationContext context,
        Set<Shape> shapes
    ) {
        for (Shape shape : getConnectedShapes(context, shapes)) {
            var deserFunction = context.protocolGenerator().getDeserializationFunction(context, shape);

            context.writerDelegator().useFileWriter(deserFunction.getDefinitionFile(),
                    deserFunction.getNamespace(), writer -> {
                shape.accept(new JsonShapeDeserVisitor(context, writer));
            });
        }
    }

    private Set<Shape> getConnectedShapes(GenerationContext context, Set<Shape> initialShapes) {
        var shapeWalker = new Walker(NeighborProviderIndex.of(context.model()).getProvider());
        var connectedShapes = new TreeSet<>(initialShapes);
        initialShapes.forEach(shape -> connectedShapes.addAll(shapeWalker.walkShapes(shape)));
        return connectedShapes;
    }

    @Override
    protected void resolveErrorCodeAndMessage(GenerationContext context, PythonWriter writer) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.protocolutils", "parse_rest_json_error_info");
        writer.write("code, message, parsed_body = await parse_rest_json_error_info(http_response)");
    }
}
