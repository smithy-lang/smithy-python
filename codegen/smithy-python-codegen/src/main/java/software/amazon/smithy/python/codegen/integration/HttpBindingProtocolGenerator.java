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


import static software.amazon.smithy.model.knowledge.HttpBinding.Location.DOCUMENT;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.LABEL;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.PAYLOAD;
import static software.amazon.smithy.model.traits.TimestampFormatTrait.Format;

import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.knowledge.HttpBinding;
import software.amazon.smithy.model.knowledge.HttpBinding.Location;
import software.amazon.smithy.model.knowledge.HttpBindingIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.pattern.SmithyPattern;
import software.amazon.smithy.model.pattern.SmithyPattern.Segment;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.NumberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.HttpTrait;
import software.amazon.smithy.model.traits.MediaTypeTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Abstract implementation useful for all protocols that use HTTP bindings.
 *
 * <p>This will implement any handling of components outside the request
 * body and error handling.
 */
@SmithyUnstableApi
public abstract class HttpBindingProtocolGenerator implements ProtocolGenerator {

    private final Set<Shape> deserializingDocumentShapes = new TreeSet<>();

    @Override
    public ApplicationProtocol getApplicationProtocol() {
        return ApplicationProtocol.createDefaultHttpApplicationProtocol();
    }

    /**
     * Gets the default serde format for timestamps.
     *
     * @return Returns the default format.
     */
    protected abstract Format getDocumentTimestampFormat();

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
                writer.pushState(new RequestSerializerSection(operation));
                writer.write("""
                    async def $L(input: $T, config: $T) -> $T:
                        ${C|}
                    """, serFunction.getName(), inputSymbol, configSymbol, transportRequest,
                    writer.consumer(w -> generateRequestSerializer(context, operation, w)));
                writer.popState();
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

        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python._private.http", "Request", "_Request");
        writer.addImport("smithy_python._private.http", "URI", "_URI");

        writer.write("""
            return _Request(
                url=_URI(
                    host="",
                    path=path,
                    scheme="https",
                    query=query,
                ),
                method=$S,
                headers=headers,
                body=body,
            )
            """, httpTrait.getMethod());
    }

    /**
     * A section that controls writing out the entire serialization function.
     *
     * @param operation The operation whose serializer is being generated.
     */
    public record RequestSerializerSection(OperationShape operation) implements CodeSection {}

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
        writer.pushState(new SerializeFieldsSection(operation));
        // TODO: map headers from inputs
        // TODO: write out default http and protocol headers
        writer.addImport("smithy_python.interfaces.http", "HeadersList", "_HeadersList");
        writer.write("headers: _HeadersList = []");
        writer.popState();
    }

    /**
     * A section that controls serializing HTTP fields, namely headers.
     *
     * <p>By default, it handles setting protocol default values and values based on
     * the smithy.api#httpHeader and smithy.api#httpPrefixHeaders traits.
     *
     * @param operation The operation whose fields section is being generated.
     */
    public record SerializeFieldsSection(OperationShape operation) implements CodeSection {}

    /**
     * Serializes the path, including resolving any path bindings.
     */
    private void serializePath(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new SerializePathSection(operation));

        // Get a map of member name to label bindings. The URI pattern we fetch uses the member name
        // for the content of label segments, so this lets us look up the extra info we need for those.
        var labelBindings = bindingIndex.getRequestBindings(operation, LABEL).stream()
            .collect(Collectors.toMap(HttpBinding::getMemberName, httpBinding -> httpBinding));

        // Build up a format string that will produce the path. We could have used an f-string, but they end up
        // taking a ton of space and aren't easily formatted. Using .format results in something that is much
        // easier to grok.
        var formatString = new StringBuilder("/");
        var uri = operation.expectTrait(HttpTrait.class).getUri();
        for (SmithyPattern.Segment segment : uri.getSegments()) {
            if (segment.isLabel()) {
                var httpBinding = labelBindings.get(segment.getContent());
                var memberName = context.symbolProvider().toMemberName(httpBinding.getMember());

                // Pattern members must be non-empty and non-none, so we assert that here.
                // Note that we've not actually started writing the format string out yet, which
                // is why we can just write out these guard clauses here.
                writer.write("""
                    if not input.$1L:
                        raise $2T("$1L must not be empty.")
                    """, memberName, CodegenUtils.getServiceError(context.settings()));

                // We're creating an f-string, so here we just put the contents inside some brackets to allow
                // for string interpolation.
                formatString.append("{");
                formatString.append(memberName);
                formatString.append("}");
            } else {
                // Static segments just get inserted literally.
                formatString.append(segment.getContent());
            }

            // Always append a forward slash. This will leave us with a trailing slash, which is what we want.
            formatString.append("/");
        }

        // Write out the f-string
        writer.openBlock("path = $S.format(", ")", formatString.toString(), () -> {
            writer.addStdlibImport("urllib.parse", "quote", "urlquote");
            for (Segment labelSegment : uri.getLabels()) {
                var httpBinding = labelBindings.get(labelSegment.getContent());
                var memberName = context.symbolProvider().toMemberName(httpBinding.getMember());

                // urllib.parse.quote will, by default, allow forward slashes. This is fine for
                // greedy labels, which are expected to contain multiple segments. But normal
                // labels aren't allowed to contain multiple segments, so we need to encode them
                // there too. We do this here by adding a conditional argument specifying no safe
                // characters.
                var urlSafe = labelSegment.isGreedyLabel() ? "" : ", safe=''";

                var dataSource = "input." + memberName;
                var target = context.model().expectShape(httpBinding.getMember().getTarget());
                    writer.write("$1L=urlquote($3L$2L),", memberName, urlSafe, getInputValue(
                        context, writer, httpBinding.getLocation(), dataSource, httpBinding.getMember(), target
                    ));
            }
        });

        writer.popState();
    }

    /**
     * A section that controls path serialization.
     *
     * <p>By default, it handles setting static values and labels based on
     * the smithy.api#http and smithy.api#httpLabel traits.
     *
     * @param operation The operation whose path section is being generated.
     */
    public record SerializePathSection(OperationShape operation) implements CodeSection {}

    /**
     * Serializes the query in the form of a list of tuples.
     */
    private void serializeQuery(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new SerializeQuerySection(operation));
        writer.write("query_params: list[tuple[str, str | None]] = []");
        // TODO: implement query serialization

        writer.write("""
            query: str = ""
            for i, param in enumerate(query_params):
                if i != 1:
                    query += "&"
                if param[1] is None:
                    query += param[0]
                else:
                    query += f"{param[0]}={param[1]}"
            """);
        writer.popState();
    }

    /**
     * A section that controls query serialization.
     *
     * <p>By default, it handles setting static values and key-value pairs based on
     * smithy.api#httpQuery and smithy.api#httpQueryParams.
     *
     * @param operation The operation whose query section is being generated.
     */
    public record SerializeQuerySection(OperationShape operation) implements CodeSection {}

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
        writer.pushState(new SerializeBodySection(operation));
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
        writer.popState();
    }

    /**
     * A section that controls serializing the request body.
     *
     * <p>By default, it handles calling out to body serialization functions for every
     * input member that is bound to the document, or which uses the smithy.api#httpPayload
     * trait.
     *
     * @param operation The operation whose body section is being generated.
     */
    public record SerializeBodySection(OperationShape operation) implements CodeSection {}

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

    /**
     * Given context and a source of data, generate an input value provider for the
     * shape. This may use native types or invoke complex type serializers to
     * manipulate the dataSource into the proper input content.
     *
     * @param context The generation context.
     * @param writer The writer this value will be written to. Used only to add
     *               imports, if necessary.
     * @param bindingType How this value is bound to the operation input.
     * @param dataSource The in-code location of the data to provide an input of
     *                   ({@code input.foo}, {@code entry}, etc.)
     * @param member The member that points to the value being provided.
     * @param target The shape of the value being provided.
     * @return Returns a value or expression of the input value.
     */
    protected String getInputValue(
        GenerationContext context,
        PythonWriter writer,
        HttpBinding.Location bindingType,
        String dataSource,
        MemberShape member,
        Shape target
    ) {
        if (target.isStringShape()) {
            return getStringInputParam(context, writer, bindingType, dataSource, member, target);
        } else if (target.isFloatShape() || target.isDoubleShape()) {
            // Using float ensures we get a decimal even if there is no fraction given
            // e.g. 1 => 1.0
            return String.format("str(float(%s))", dataSource);
        } else if (target instanceof NumberShape) {
            return String.format("str(%s)", dataSource);
        } else if (target.isBooleanShape()) {
            return String.format("('true' if %s else 'false')", dataSource);
        } else if (target.isTimestampShape()) {
            return getTimestampInputParam(context, writer, bindingType, dataSource, member, target);
        } else {
            // TODO: add support here for other shape types
            return dataSource;
        }
//        throw new CodegenException(String.format(
//            "Unsupported %s binding of %s to %s in %s using the %s protocol",
//            bindingType, member.getMemberName(), target.getType(), member.getContainer(), getName()));
    }

    /**
     * Given context and a source of data, generate an input value provider for a
     * string. By default, this base64 encodes content in headers if there is a
     * mediaType applied to the string, and passes through for all other cases.
     *
     * @param context The generation context.
     * @param writer The writer this value will be written to. Used only to add
     *               imports, if necessary.
     * @param bindingType How this value is bound to the operation input.
     * @param dataSource The in-code location of the data to provide an input of
     *                   ({@code input.foo}, {@code entry}, etc.)
     * @param target The shape of the value being provided.
     * @return Returns a value or expression of the input string.
     */
    protected String getStringInputParam(
        GenerationContext context,
        PythonWriter writer,
        HttpBinding.Location bindingType,
        String dataSource,
        MemberShape member,
        Shape target
    ) {
        if (bindingType == Location.HEADER) {
            if (target.hasTrait(MediaTypeTrait.class)) {
                writer.addStdlibImport("base64", "b64encode");
                return "b64encode(" + dataSource + "))";
            }
        }
        return dataSource;
    }

    /**
     * Given context and a source of data, generate an input value provider for the
     * shape. This uses the format specified, converting to strings when in a header,
     * label, or query string.
     *
     * @param context The generation context.
     * @param writer The writer this value will be written to. Used only to add
     *               imports, if necessary.
     * @param bindingType How this value is bound to the operation input.
     * @param dataSource The in-code location of the data to provide an input of
     *                   ({@code input.foo}, {@code entry}, etc.)
     * @param member The member that points to the value being provided.
     * @return Returns a value or expression of the input shape.
     */
    protected String getTimestampInputParam(
        GenerationContext context,
        PythonWriter writer,
        HttpBinding.Location bindingType,
        String dataSource,
        MemberShape member,
        Shape target
    ) {
        var httpIndex = HttpBindingIndex.of(context.model());
        var format = switch (bindingType) {
            case HEADER -> httpIndex.determineTimestampFormat(member, bindingType, Format.HTTP_DATE);
            case LABEL -> httpIndex.determineTimestampFormat(member, bindingType, getDocumentTimestampFormat());
            case QUERY -> httpIndex.determineTimestampFormat(member, bindingType, Format.DATE_TIME);
            default ->
                throw new CodegenException("Unexpected named member shape binding location `" + bindingType + "`");
        };

        return HttpProtocolGeneratorUtils.getTimestampInputParam(
            context, writer, dataSource, member, format);
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
                writer.pushState(new ResponseDeserializerSection(operation));
                writer.write("""
                    async def $L(http_response: $T, config: $T) -> $T:
                        ${C|}
                    """, deserFunction.getName(), transportResponse, configSymbol, outputSymbol,
                    writer.consumer(w -> generateResponseDeserializer(context, writer, operation)));
                writer.popState();
            });
        }
        generateDocumentBodyShapeDeserializers(context, deserializingDocumentShapes);
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
        writer.write("kwargs: dict[str, Any] = {}");
        var bindingIndex = HttpBindingIndex.of(context.model());

        deserializeBody(context, writer, operation, bindingIndex);
        deserializeHeaders(context, writer, operation, bindingIndex);
        deserializeStatusCode(context, writer, operation, bindingIndex);

        var outputShape = context.model().expectShape(operation.getOutputShape());
        var outputSymbol = context.symbolProvider().toSymbol(outputShape);
        writer.write("return $T(**kwargs)", outputSymbol);
    }

    /**
     * A section that controls writing out the entire deserialization function.
     *
     * @param operation The operation whose deserializer is being generated.
     */
    public record ResponseDeserializerSection(OperationShape operation) implements CodeSection {}

    private void deserializeHeaders(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeFieldsSection(operation));
        // TODO: implement header deserialization
        writer.popState();
    }

    /**
     * A section that controls deserializing HTTP fields, namely headers.
     *
     * <p>By default, it handles values based on smithy.api#httpHeader and
     * smithy.api#httpPrefixHeaders traits.
     *
     * @param operation The operation whose fields section is being generated.
     */
    public record DeserializeFieldsSection(OperationShape operation) implements CodeSection {}

    private void deserializeStatusCode(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeStatusCodeSection(operation));
        var statusBinding = bindingIndex.getResponseBindings(operation, Location.RESPONSE_CODE);
        if (!statusBinding.isEmpty()) {
            var statusMember = context.symbolProvider().toMemberName(statusBinding.get(0).getMember());
            writer.write("kwargs[$S] = http_response.status_code", statusMember);
        }
        writer.popState();
    }

    /**
     * A section that controls deserializing the HTTP status code.
     *
     * @param operation The operation whose status code section is being generated.
     */
    public record DeserializeStatusCodeSection(OperationShape operation) implements CodeSection {}

    private void deserializeBody(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeBodySection(operation));
        // TODO: implement body deserialization
        var documentBindings = bindingIndex.getResponseBindings(operation, DOCUMENT);
        if (!documentBindings.isEmpty() || shouldWriteDefaultBody(context, operation)) {
            deserializeDocumentBody(context, writer, operation, documentBindings);
            for (HttpBinding binding : documentBindings) {
                var target = context.model().expectShape(binding.getMember().getTarget());
                deserializingDocumentShapes.add(target);
            }
        }

        var payloadBindings = bindingIndex.getResponseBindings(operation, PAYLOAD);
        if (!payloadBindings.isEmpty()) {
            var binding = payloadBindings.get(0);
            deserializePayloadBody(context, writer, operation, binding);
            var target = context.model().expectShape(binding.getMember().getTarget());
            deserializingDocumentShapes.add(target);
        }
        writer.popState();
    }

    /**
     * A section that controls deserializing the response body.
     *
     * <p>By default, it handles calling out to body deserialization functions for every
     * output member that is bound to the document, or which uses the smithy.api#httpPayload
     * trait.
     *
     * @param operation The operation whose body section is being generated.
     */
    public record DeserializeBodySection(OperationShape operation) implements CodeSection {}

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
     *     kwargs['spam'] = data['spam']
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
     * Generates deserialization functions for shapes in the given set.
     *
     * <p>These are the functions that deserializeDocumentBody will call out to.
     *
     * @param context The generation context.
     * @param shapes The shapes to generate deserialization for.
     */
    protected abstract void generateDocumentBodyShapeDeserializers(
        GenerationContext context,
        Set<Shape> shapes
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
