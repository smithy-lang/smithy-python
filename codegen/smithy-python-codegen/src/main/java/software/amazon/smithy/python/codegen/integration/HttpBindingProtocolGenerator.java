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


import static java.lang.String.format;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.DOCUMENT;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.PAYLOAD;

import java.util.List;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.knowledge.HttpBindingIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.traits.HttpTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Abstract implementation useful for all protocols that use HTTP bindings.
 *
 * <p>This will implement any handling of components outside the request
 * body and error handling.
 */
@SmithyUnstableApi
public abstract class HttpBindingProtocolGenerator implements ProtocolGenerator {

    @Override
    public ApplicationProtocol getApplicationProtocol() {
        return ApplicationProtocol.createDefaultHttpApplicationProtocol();
    }

    /**
     * Given a context and operation, should a default input body be written.
     *
     * <p>By default, no body will be written if there are no members bound to the input.
     *
     * @param context The generation context.
     * @param operation The operation whose input is being serialized.
     * @return True if a default body should be generated.
     */
    protected boolean shouldWriteDefaultBody(GenerationContext context, OperationShape operation) {
        return HttpBindingIndex.of(context.model()).getRequestBindings(operation).isEmpty();
    }

    @Override
    public void generateSharedSerializerComponents(GenerationContext context) {
        // TODO: remove this when we have a concrete implementation to use
        var filename = format("./%s/serialize.py", context.settings().getModuleName());
        context.writerDelegator().useFileWriter(filename, writer -> {
            writer.addStdlibImport("dataclasses", "dataclass");
            writer.write("""
                @dataclass
                class URL:
                    scheme: str
                    hostname: str
                    port: int | None
                    path: str
                    query_params: list[tuple[str, str]]


                @dataclass
                class Request:
                    url: URL
                    method: str
                    headers: list[tuple[str, str]]
                    body: Any
                """);
        });
    }

    @Override
    public void generateRequestSerializers(GenerationContext context) {
        var topDownIndex = TopDownIndex.of(context.model());
        var delegator = context.writerDelegator();
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var transportRequest = context.applicationProtocol().requestType();
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().getService())) {
            var serFunction = getSerializationFunction(context, operation);
            var input = context.model().expectShape(operation.getInputShape());
            var inputSymbol = context.symbolProvider().toSymbol(input);
            delegator.useFileWriter(serFunction.getDefinitionFile(), serFunction.getNamespace(), writer -> {
                writer.write("""
                    async def $L(input: $T, config: $T) -> $T:
                        ${C|}
                    """, serFunction.getName(), inputSymbol, configSymbol, transportRequest,
                    writer.consumer(w -> generateRequestSerializer(context, operation, w)));
            });
        }
    }

    /**
     * Generates the content of the operation request serializer.
     *
     * <p>Serialization of the http-level components will be inline
     * since there isn't any use for them elsewhere. Serialization
     * of document body components should be delegated, however,
     * as they will need to be re-used in all likelihood.
     *
     * <p>This function has the following in scope:
     * <ul>
     *     <li>input - the operation's input</li>
     *     <li>config - the client config</li>
     * </ul>
     */
    private void generateRequestSerializer(
        GenerationContext context,
        OperationShape operation,
        PythonWriter writer
    ) {
        var httpTrait = operation.expectTrait(HttpTrait.class);
        var bindingIndex = HttpBindingIndex.of(context.model());
        serializeHeaders(context, writer, operation, bindingIndex);
        serializePath(context, writer, operation, bindingIndex);
        serializeQuery(context, writer, operation, bindingIndex);
        serializeBody(context, writer, operation, bindingIndex);

        writer.write("""
            return Request(
                url=URL(
                    scheme="https",
                    hostname="",
                    port=None,
                    path=path,
                    query_params=query_params,
                ),
                method=$S,
                headers=headers,
                body=body,
            )
            """, httpTrait.getMethod());
    }

    /**
     * Serializes headers, including standard headers like content-type
     * and protocol-specific standard headers.
     */
    private void serializeHeaders(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: map headers from inputs
        // TODO: write out default http and protocol headers
        writer.write("headers: list[tuple[str, str]] = []");
    }

    /**
     * Serializes the path, including resolving any path bindings.
     */
    private void serializePath(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: map path entries from input
        writer.write("path: str = '/'");
    }

    /**
     * Serializes the query in the form of a list of tuples.
     */
    private void serializeQuery(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: implement query serialization
        writer.write("query_params: list[tuple[str, str]] = []");
    }

    /**
     * Orchestrates body serialization.
     *
     * <p>The format of the body is going to be dependent on the specific
     * protocol, so this delegates out to implementors.
     */
    private void serializeBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.addStdlibImport("typing", "Any");
        writer.write("body: Any = b''");

        var documentBindings = bindingIndex.getRequestBindings(operation, DOCUMENT);
        if (!documentBindings.isEmpty() || shouldWriteDefaultBody(context, operation)) {
            serializeDocumentBody(context, writer, operation, documentBindings);
        }

        var payloadBindings = bindingIndex.getRequestBindings(operation, PAYLOAD);
        if (!payloadBindings.isEmpty()) {
            serializePayloadBody(context, writer, operation, payloadBindings.get(0));
        }
    }

    /**
     * Writes the code needed to serialize a protocol input document.
     *
     * <p>Implementations of this method are expected to set a value to the
     * {@code body} variable that will be serialized as the request body.
     * This variable will already be defined in scope.
     *
     * <p>Implementations MUST properly fill the body parameter even if no
     * document bindings are present.
     *
     * <p>For example:
     *
     * <pre>{@code
     * body_params: dict[str, Any] = {}
     *
     * if input.spam:
     *   body_params['spam'] = input.spam;
     *
     * body = json.dumps(body_params).encode('utf-8');
     * }</pre>
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param operation The operation whose input is being generated.
     * @param documentBindings The bindings to place in the document.
     */
    protected abstract void serializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    );


    /**
     * Writes the code needed to serialize the input payload of a request.
     *
     * <p>Implementations of this method are expected to set a value to the
     * {@code body} variable that will be serialized as the request body.
     * This variable will already be defined in scope.
     *
     * <p>For example:
     *
     * <pre>{@code
     * body = b64encode(input.body)
     * }</pre>
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param operation The operation whose input is being generated.
     * @param payloadBinding The payload binding to serialize.
     */
    protected void serializePayloadBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBinding payloadBinding
    ) {
        // TODO: implement this
    }

    @Override
    public void generateResponseDeserializers(GenerationContext context) {
        // TODO: Generate deserializers for http bindings, e.g. non-body parts of the http response
        var topDownIndex = TopDownIndex.of(context.model());
        var delegator = context.writerDelegator();
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var transportResponse = context.applicationProtocol().responseType();
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().getService())) {
            var deserFunction = getDeserializationFunction(context, operation);
            var output = context.model().expectShape(operation.getOutputShape());
            var outputSymbol = context.symbolProvider().toSymbol(output);
            delegator.useFileWriter(deserFunction.getDefinitionFile(), deserFunction.getNamespace(), writer -> {
                writer.write("""
                    async def $L(http_response: $T, config: $T) -> $T:
                        ${C|}
                    """, deserFunction.getName(), transportResponse, configSymbol, outputSymbol,
                    writer.consumer(w -> generateResponseDeserializer(context, writer, operation)));
            });
        }
    }

    /**
     * Generates the content of the operation response deserializer.
     *
     * <p>Deserialization of the http-level components will be inline
     * since there isn't any use for them elsewhere. Deserialization
     * of document body components should be delegated, however,
     * as they will need to be re-used in all likelihood.
     *
     * <p>This function has the following in scope:
     * <ul>
     *     <li>http_response - the http-level response</li>
     *     <li>config - the client config</li>
     * </ul>
     */
    private void generateResponseDeserializer(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation
    ) {
        writer.addStdlibImport("typing", "Any");
        writer.write("args: dict[str, Any] = {}");
        var bindingIndex = HttpBindingIndex.of(context.model());

        deserializeBody(context, writer, operation, bindingIndex);
        deserializeHeaders(context, writer, operation, bindingIndex);
        deserializeStatusCode(context, writer, operation, bindingIndex);

        var outputShape = context.model().expectShape(operation.getOutputShape());
        var outputSymbol = context.symbolProvider().toSymbol(outputShape);
        writer.write("return $T(**args)", outputSymbol);
    }

    private void deserializeHeaders(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: implement header deserialization
    }

    private void deserializeStatusCode(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: implement status code deserialization
    }

    private void deserializeBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        // TODO: implement body deserialization
        var documentBindings = bindingIndex.getResponseBindings(operation, DOCUMENT);
        if (!documentBindings.isEmpty() || shouldWriteDefaultBody(context, operation)) {
            deserializeDocumentBody(context, writer, operation, documentBindings);
        }

        var payloadBindings = bindingIndex.getResponseBindings(operation, PAYLOAD);
        if (!payloadBindings.isEmpty()) {
            deserializePayloadBody(context, writer, operation, payloadBindings.get(0));
        }
    }

    /**
     * Writes the code needed to deserialize a protocol output document.
     *
     * <p>The contents of the response body will be available in the
     * {@code http_response} variable.
     *
     * <p>For example:
     *
     * <pre>{@code
     * data = json.loads(http_response.body.read().decode('utf-8'))
     * if 'spam' in data:
     *     args['spam'] = data['spam']
     * }</pre>
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param operation The operation whose output document is being deserialized.
     * @param documentBindings The bindings to read from the document.
     */
    protected abstract void deserializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        List<HttpBinding> documentBindings
    );

    /**
     * Writes the code needed to deserialize the output payload of a response.
     *
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param operation The operation whose output payload is being deserialized.
     * @param binding The payload binding to deserialize.
     */
    protected void deserializePayloadBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBinding binding
    ) {
        // TODO: implement payload deserialization
        // This will have a default implementation since it'll mostly be standard
    }
}
