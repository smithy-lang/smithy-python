/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestCase;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestCase;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.HttpProtocolTestGenerator;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SetUtils;
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

    @Override
    public ShapeId getProtocol() {
        return RestJson1Trait.ID;
    }

    @Override
    protected Format getDocumentTimestampFormat() {
        return Format.EPOCH_SECONDS;
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
        if (shape.hasTrait(ErrorTrait.class)) {
            // Error handling isn't implemented yet
            return true;
        }
        if (testCase instanceof HttpRequestTestCase) {
            // Request serialization isn't finished, so here we only test the bindings that are supported.
            Set<Location> implementedBindings = SetUtils.of(Location.LABEL);
            var bindingIndex = HttpBindingIndex.of(context.model());

            // If any member specified in the test is bound to a location we haven't yet implemented,
            // skip the test.
            var supportedMembers = bindingIndex.getRequestBindings(shape).values().stream()
                .filter(binding -> implementedBindings.contains(binding.getLocation()))
                .map(binding -> binding.getMember().getMemberName())
                .collect(Collectors.toSet());
            for (StringNode setMember : testCase.getParams().getMembers().keySet()) {
                if (!supportedMembers.contains(setMember.getValue())) {
                    return true;
                }
            }
        }
        if (testCase instanceof HttpResponseTestCase) {
            var bindingIndex = HttpBindingIndex.of(context.model());
            return bindingIndex.getResponseBindings(shape, Location.PAYLOAD).size() != 0;
        }
        return false;
    }

    @Override
    protected void serializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    ) {
        // TODO: implement this
        writer.write("body = b'{}'");
    }

    @Override
    protected void deserializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    ) {
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addStdlibImport("json", "loads", "json_loads");

        writer.write("""
            body = await http_response.body.read()
            output = json_loads(body) if body else {}

            """);

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
        var shapeWalker = new Walker(NeighborProviderIndex.of(context.model()).getProvider());
        var shapesToGenerate = new TreeSet<>(shapes);
        shapes.forEach(shape -> shapesToGenerate.addAll(shapeWalker.walkShapes(shape)));

        for (Shape shape : shapesToGenerate) {
            var deserFunction = context.protocolGenerator().getDeserializationFunction(context, shape);

            context.writerDelegator().useFileWriter(deserFunction.getDefinitionFile(),
                    deserFunction.getNamespace(), writer -> {
                shape.accept(new JsonShapeDeserVisitor(context, writer));
            });
        }
    }
}
