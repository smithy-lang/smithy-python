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
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.HEADER;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.LABEL;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.PAYLOAD;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.PREFIX_HEADERS;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.QUERY;
import static software.amazon.smithy.model.knowledge.HttpBinding.Location.QUERY_PARAMS;
import static software.amazon.smithy.model.traits.TimestampFormatTrait.Format;
import static software.amazon.smithy.python.codegen.integration.HttpProtocolGeneratorUtils.generateErrorDispatcher;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
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
import software.amazon.smithy.model.shapes.BigDecimalShape;
import software.amazon.smithy.model.shapes.BigIntegerShape;
import software.amazon.smithy.model.shapes.BlobShape;
import software.amazon.smithy.model.shapes.BooleanShape;
import software.amazon.smithy.model.shapes.ByteShape;
import software.amazon.smithy.model.shapes.DoubleShape;
import software.amazon.smithy.model.shapes.FloatShape;
import software.amazon.smithy.model.shapes.IntegerShape;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.LongShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ShapeVisitor;
import software.amazon.smithy.model.shapes.ShortShape;
import software.amazon.smithy.model.shapes.StringShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.TimestampShape;
import software.amazon.smithy.model.traits.HttpTrait;
import software.amazon.smithy.model.traits.MediaTypeTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonWriter;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.StringUtils;

/**
 * Abstract implementation useful for all protocols that use HTTP bindings.
 *
 * <p>This will implement any handling of components outside the request
 * body and error handling.
 */
@SmithyUnstableApi
public abstract class HttpBindingProtocolGenerator implements ProtocolGenerator {

    private final Set<Shape> serializingDocumentShapes = new TreeSet<>();
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
        generateDocumentBodyShapeSerializers(context, serializingDocumentShapes);
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
        serializePath(context, writer, operation, bindingIndex);
        serializeQuery(context, writer, operation, bindingIndex);
        serializeBody(context, writer, operation, bindingIndex);
        serializeHeaders(context, writer, operation, bindingIndex);

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
        writer.addImport("smithy_python.interfaces.http", "HeadersList", "_HeadersList");
        writer.write("""
            headers: _HeadersList = [
                ${C|}
                ${C|}
                ${C|}
            ]

            """,
            writer.consumer(w -> writeContentType(context, w, operation)),
            writer.consumer(w -> writeContentLength(context, w, operation)),
            writer.consumer(w -> writeDefaultHeaders(context, w, operation)));
            serializeIndividualHeaders(context, writer, operation);
            serializePrefixHeaders(context, writer, operation);
        writer.popState();
    }

    /**
     * Gets the default content-type when a document is synthesized in the body.
     *
     * @return Returns the default content-type.
     */
    protected abstract String getDocumentContentType();

    private void writeContentType(GenerationContext context, PythonWriter writer, OperationShape operation) {
        if (isStreamingPayloadInput(context, operation)) {
            return;
        }
        var httpIndex = HttpBindingIndex.of(context.model());
        var optionalContentType = httpIndex.determineRequestContentType(operation, getDocumentContentType());
        if (optionalContentType.isEmpty() && shouldWriteDefaultBody(context, operation)) {
            optionalContentType = Optional.of(getDocumentContentType());
        }
        optionalContentType.ifPresent(contentType -> writer.write("('Content-Type', $S),", contentType));
    }

    private void writeContentLength(GenerationContext context, PythonWriter writer, OperationShape operation) {
        if (isStreamingPayloadInput(context, operation)) {
            return;
        }
        var hasBodyBindings = HttpBindingIndex.of(context.model())
            .getRequestBindings(operation).values().stream()
            .anyMatch(binding -> binding.getLocation() == PAYLOAD || binding.getLocation() == DOCUMENT);

        if (hasBodyBindings) {
            writer.write("('Content-Length', str(len(body))),");
        }
    }

    private boolean isStreamingPayloadInput(GenerationContext context, OperationShape operation) {
        var payloadBinding = HttpBindingIndex.of(context.model()).getRequestBindings(operation, PAYLOAD);
        if (payloadBinding.isEmpty()) {
            return false;
        }
        return payloadBinding.get(0).getMember().getMemberTrait(context.model(), StreamingTrait.class).isPresent();
    }

    /**
     * Writes any additional HTTP input headers required by the protocol implementation.
     *
     * @param context The generation context.
     * @param writer The writer to write to.
     * @param operation The operation whose input is being generated.
     */
    protected void writeDefaultHeaders(GenerationContext context, PythonWriter writer, OperationShape operation) {
    }

    private void serializeIndividualHeaders(GenerationContext context, PythonWriter writer, OperationShape operation) {
        var index = HttpBindingIndex.of(context.model());
        var headerBindings = index.getRequestBindings(operation, HEADER);
        for (HttpBinding binding : headerBindings) {
            var target = context.model().expectShape(binding.getMember().getTarget());
            boolean accessFalsey = !(target.isStringShape() || target.isListShape());

            CodegenUtils.accessStructureMember(context, writer, "input", binding.getMember(), accessFalsey, () -> {
                var pythonName = context.symbolProvider().toMemberName(binding.getMember());

                if (target.isListShape()) {
                    var listMember = target.asListShape().get().getMember();
                    var listTarget = context.model().expectShape(listMember.getTarget());
                    var inputValue = listTarget.accept(new HttpMemberSerVisitor(
                        context, writer, binding.getLocation(), "e", listMember,
                        getDocumentTimestampFormat()));

                    var trailer = listTarget.isStringShape() ? " if e" : "";
                    writer.write("""
                        headers.extend(($S, $L) for e in input.$L$L)
                        """, binding.getLocationName(), inputValue, pythonName, trailer);
                } else {
                    var dataSource = "input." + pythonName;
                    var inputValue = target.accept(new HttpMemberSerVisitor(
                        context, writer, binding.getLocation(), dataSource, binding.getMember(),
                        getDocumentTimestampFormat()));
                    writer.write("headers.append(($S, $L))", binding.getLocationName(), inputValue);
                }
            });
        }
    }

    private void serializePrefixHeaders(GenerationContext context, PythonWriter writer, OperationShape operation) {
        var index = HttpBindingIndex.of(context.model());
        var prefixHeaderBindings = index.getRequestBindings(operation, PREFIX_HEADERS);
        for (HttpBinding binding : prefixHeaderBindings) {
            CodegenUtils.accessStructureMember(context, writer, "input", binding.getMember(), () -> {
                var pythonName = context.symbolProvider().toMemberName(binding.getMember());
                var target = context.model().expectShape(binding.getMember().getTarget(), MapShape.class);
                var valueTarget = context.model().expectShape(target.getValue().getTarget());
                var inputValue = valueTarget.accept(new HttpMemberSerVisitor(
                    context, writer, binding.getLocation(), "v", target.getValue(),
                    getDocumentTimestampFormat()));
                writer.write("""
                    headers.extend((f'$L{k}', $L) for k, v in input.$L.items() if v)
                    """, binding.getLocationName(
                ), inputValue, pythonName);
            });
        }

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
        var formatString = new StringBuilder();
        var uri = operation.expectTrait(HttpTrait.class).getUri();
        for (SmithyPattern.Segment segment : uri.getSegments()) {
            formatString.append("/");
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
        }

        if (uri.getLabels().isEmpty()) {
            writer.write("path = $S", formatString.toString());
            writer.popState();
            return;
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
                var inputValue = target.accept(new HttpMemberSerVisitor(
                    context, writer, httpBinding.getLocation(), dataSource, httpBinding.getMember(),
                    getDocumentTimestampFormat()));
                writer.write("$1L=urlquote($3L$2L),", memberName, urlSafe, inputValue);
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
        writer.writeInline("query_params: list[tuple[str, str | None]] = [");
        var httpTrait = operation.expectTrait(HttpTrait.class);
        for (Map.Entry<String, String> entry : httpTrait.getUri().getQueryLiterals().entrySet()) {
            if (StringUtils.isBlank(entry.getValue())) {
                writer.write("($S, None),", entry.getKey());
            } else {
                writer.write("($S, $S),", entry.getKey(), entry.getValue());
            }
        }
        writer.write("]\n");

        serializeIndividualQueryParams(context, writer, operation, bindingIndex);
        serializeQueryParamsMap(context, writer, operation, bindingIndex);

        writer.addStdlibImport("urllib.parse", "quote", "urlquote");
        writer.write("""
            query: str = ""
            for i, param in enumerate(query_params):
                if i != 0:
                    query += "&"
                if param[1] is None:
                    query += urlquote(param[0], safe='')
                else:
                    query += f"{urlquote(param[0], safe='')}={urlquote(param[1], safe='')}"
            """);
        writer.popState();
    }

    private void serializeIndividualQueryParams(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        var queryBindings = bindingIndex.getRequestBindings(operation, QUERY);
        for (HttpBinding binding : queryBindings) {
            var memberName = context.symbolProvider().toMemberName(binding.getMember());
            var locationName = binding.getLocationName();
            var target = context.model().expectShape(binding.getMember().getTarget());

            CodegenUtils.accessStructureMember(context, writer, "input", binding.getMember(), () -> {
                if (target.isListShape()) {
                    var listMember = target.asListShape().get().getMember();
                    var listTarget = context.model().expectShape(listMember.getTarget());
                    var memberSerializer = listTarget.accept(new HttpMemberSerVisitor(
                        context, writer, QUERY, "e", listMember,
                        getDocumentTimestampFormat()));
                    writer.write("query_params.extend(($S, $L) for e in input.$L)",
                        locationName, memberSerializer, memberName);
                } else {
                    var memberSerializer = target.accept(new HttpMemberSerVisitor(
                        context, writer, QUERY, "input." + memberName, binding.getMember(),
                        getDocumentTimestampFormat()));
                    writer.write("query_params.append(($S, $L))", locationName, memberSerializer);
                }
            });
        }
    }

    private void serializeQueryParamsMap(
        GenerationContext context,
        PythonWriter writer,
        OperationShape operation,
        HttpBindingIndex bindingIndex
    ) {
        var queryMapBindings = bindingIndex.getRequestBindings(operation, QUERY_PARAMS);
        for (HttpBinding binding : queryMapBindings) {
            var memberName = context.symbolProvider().toMemberName(binding.getMember());
            var mapShape = context.model().expectShape(binding.getMember().getTarget(), MapShape.class);
            var mapTarget = context.model().expectShape(mapShape.getValue().getTarget());

            CodegenUtils.accessStructureMember(context, writer, "input", binding.getMember(), () -> {
                if (mapTarget.isListShape()) {
                    var listMember = mapTarget.asListShape().get().getMember();
                    var listMemberTarget = context.model().expectShape(listMember.getTarget());
                    var memberSerializer = listMemberTarget.accept(new HttpMemberSerVisitor(
                        context, writer, QUERY, "v", listMember,
                        getDocumentTimestampFormat()));
                    writer.write("query_params.extend((k, $1L) for k in input.$2L for v in input.$2L[k])",
                        memberSerializer, memberName);
                } else {
                    var memberSerializer = mapTarget.accept(new HttpMemberSerVisitor(
                        context, writer, QUERY, "v", mapShape.getValue(),
                        getDocumentTimestampFormat()));
                    writer.write("query_params.extend((k, $L) for k, v in input.$L.items())",
                        memberSerializer, memberName);
                }
            });
        }
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
            for (HttpBinding binding : documentBindings) {
                var target = context.model().expectShape(binding.getMember().getTarget());
                serializingDocumentShapes.add(target);
            }
        }

        var payloadBindings = bindingIndex.getRequestBindings(operation, PAYLOAD);
        if (!payloadBindings.isEmpty()) {
            var binding = payloadBindings.get(0);
            serializePayloadBody(context, writer, operation, binding);
            var target = context.model().expectShape(binding.getMember().getTarget());
            serializingDocumentShapes.add(target);
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
     * Generates serialization functions for shapes in the given set.
     *
     * <p>These are the functions that serializeDocumentBody will call out to.
     *
     * @param context The generation context.
     * @param shapes The shapes to generate deserialization for.
     */
    protected abstract void generateDocumentBodyShapeSerializers(
        GenerationContext context,
        Set<Shape> shapes
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
        var topDownIndex = TopDownIndex.of(context.model());
        var service = context.settings().getService(context.model());
        var deserializingErrorShapes = new TreeSet<ShapeId>();
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().getService())) {
            generateOperationResponseDeserializer(context, operation);
            deserializingErrorShapes.addAll(operation.getErrors(service));
        }
        for (ShapeId errorId : deserializingErrorShapes) {
            var error = context.model().expectShape(errorId, StructureShape.class);
            generateErrorResponseDeserializer(context, error);
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
    private void generateOperationResponseDeserializer(
        GenerationContext context,
        OperationShape operation
    ) {
        var delegator = context.writerDelegator();
        var deserFunction = getDeserializationFunction(context, operation);
        var output = context.model().expectShape(operation.getOutputShape());
        var outputSymbol = context.symbolProvider().toSymbol(output);
        var transportResponse = context.applicationProtocol().responseType();
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var httpTrait = operation.expectTrait(HttpTrait.class);
        var errorFunction = context.protocolGenerator().getErrorDeserializationFunction(context, operation);
        delegator.useFileWriter(deserFunction.getDefinitionFile(), deserFunction.getNamespace(), writer -> {
            writer.pushState(new ResponseDeserializerSection(operation));
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                async def $L(http_response: $T, config: $T) -> $T:
                    if http_response.status_code != $L and http_response.status_code >= 300:
                        raise await $T(http_response, config)

                    kwargs: dict[str, Any] = {}

                    ${C|}

                """, deserFunction.getName(), transportResponse, configSymbol,
                outputSymbol, httpTrait.getCode(), errorFunction,
                writer.consumer(w -> generateHttpResponseDeserializer(context, writer, operation)));
            writer.popState();
        });
        generateErrorDispatcher(context, operation, this::getErrorCode, this::resolveErrorCodeAndMessage);
    }

    /**
     * A section that controls writing out the entire deserialization function for an operation.
     *
     * @param operation The operation whose deserializer is being generated.
     */
    public record ResponseDeserializerSection(OperationShape operation) implements CodeSection {}

    private void generateErrorResponseDeserializer(GenerationContext context, StructureShape error) {
        var deserFunction = getErrorDeserializationFunction(context, error);
        var errorSymbol = context.symbolProvider().toSymbol(error);
        var delegator = context.writerDelegator();
        var transportResponse = context.applicationProtocol().responseType();
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        delegator.useFileWriter(deserFunction.getDefinitionFile(), deserFunction.getNamespace(), writer -> {
            writer.pushState(new ErrorDeserializerSection(error));
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                async def $L(
                    http_response: $T,
                    config: $T,
                    parsed_body: Document | None,
                    default_message: str,
                ) -> $T:
                    kwargs: dict[str, Any] = {"message": default_message}

                    ${C|}

                """, deserFunction.getName(), transportResponse, configSymbol, errorSymbol,
                writer.consumer(w -> generateHttpResponseDeserializer(context, writer, error)));
            writer.popState();
        });
    }

    /**
     * A section that controls writing out the entire deserialization function for an error.
     *
     * @param error The error whose deserializer is being generated.
     */
    public record ErrorDeserializerSection(StructureShape error) implements CodeSection {}

    private void generateHttpResponseDeserializer(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError
    ) {
        var bindingIndex = HttpBindingIndex.of(context.model());

        var outputShape = operationOrError;
        if (operationOrError.isOperationShape()) {
            outputShape = context.model().expectShape(operationOrError.asOperationShape().get().getOutputShape());
        }
        var outputSymbol = context.symbolProvider().toSymbol(outputShape);

        writer.write("""
            ${C|}

            ${C|}

            ${C|}

            return $T(**kwargs)
            """,
            writer.consumer(w -> deserializeBody(context, w, operationOrError, bindingIndex)),
            writer.consumer(w -> deserializeHeaders(context, w, operationOrError, bindingIndex)),
            writer.consumer(w -> deserializeStatusCode(context, w, operationOrError, bindingIndex)),
            outputSymbol);
    }

    /**
     * Maps error shapes to their error codes.
     *
     * <p>By default, this returns the error shape's name.
     *
     * @param error The error shape.
     * @return The wire code matching the error shape.
     */
    protected String getErrorCode(StructureShape error) {
        return error.getId().getName();
    }

    /**
     * Resolves the error code and message into the {@literal code} and {@literal message}
     * variables, respectively.
     *
     * @param context The generation context.
     * @param writer The writer to write to.
     */
    protected abstract void resolveErrorCodeAndMessage(
        GenerationContext context,
        PythonWriter writer
    );

    private void deserializeHeaders(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeFieldsSection(operationOrError));
        var individualBindings = bindingIndex.getResponseBindings(operationOrError, HEADER);
        var prefixBindings = bindingIndex.getResponseBindings(operationOrError, PREFIX_HEADERS);

        if (!individualBindings.isEmpty() || !prefixBindings.isEmpty()) {
            writer.write("""
            for key, value in http_response.headers:
                _key_lowercase = key.lower()
                ${C|}
                ${C|}
            """,
                writer.consumer(w -> deserializeIndividualHeaders(context, w, individualBindings)),
                writer.consumer(w -> deserializePrefixHeaders(context, w, prefixBindings))
            );
        }

        writer.popState();
    }

    /**
     * This implements deserialization for the {@literal httpHeader} trait.
     *
     * <p>See also: <a href="https://smithy.io/2.0/spec/http-bindings.html#httpheader-trait">Smithy httpHeader docs</a>
     */
    private void deserializeIndividualHeaders(
        GenerationContext context,
        PythonWriter writer,
        List<HttpBinding> bindings
    ) {
        if (bindings.isEmpty()) {
            return;
        }
        writer.openBlock("match _key_lowercase:", "", () -> {
            for (HttpBinding binding : bindings) {
                // The httpHeader trait can be bound to a list, but not other
                // collection types.
                var target = context.model().expectShape(binding.getMember().getTarget());
                var memberName = context.symbolProvider().toMemberName(binding.getMember());
                var locationName = binding.getLocationName().toLowerCase(Locale.US);
                var deserVisitor = new HttpMemberDeserVisitor(
                    context, writer, binding.getLocation(), "value", binding.getMember(),
                    getDocumentTimestampFormat()
                );
                var targetHandler = target.accept(deserVisitor);
                if (target.isListShape()) {
                    // A header list can be a comma-delimited single entry, a set of entries with
                    // the same header key, or a combination of the two.
                    writer.write("""
                    case $1S:
                        _$2L = $3L
                        if $2S not in kwargs:
                            kwargs[$2S] = _$2L
                        else:
                            kwargs[$2S].extend(_$2L)

                    """, locationName, memberName, targetHandler);
                } else {
                    writer.write("""
                    case $1S:
                        kwargs[$2S] = $3L

                    """, locationName, memberName, targetHandler);
                }
            }
        });

    }

    /**
     * This implements deserialization for the {@literal httpPrefixHeaders} trait.
     *
     * <p>See also: <a href="https://smithy.io/2.0/spec/http-bindings.html#httpprefixheaders-trait">Smithy
     * httpPrefixHeaders docs</a>
     */
    private void deserializePrefixHeaders(
        GenerationContext context,
        PythonWriter writer,
        List<HttpBinding> bindings
    ) {
        for (HttpBinding binding : bindings) {
            var bindingTarget = context.model().expectShape(binding.getMember().getTarget()).asMapShape().get();
            var mapTarget = context.model().expectShape(bindingTarget.getValue().getTarget());
            var memberName = context.symbolProvider().toMemberName(binding.getMember());
            var locationName = binding.getLocationName().toLowerCase(Locale.US);
            var deserVisitor = new HttpMemberDeserVisitor(
                context, writer, binding.getLocation(), "value", bindingTarget.getValue(),
                getDocumentTimestampFormat()
            );
            // Prefix headers can only be maps of string to string, and they can't be sparse.
            writer.write("""
                if _key_lowercase.startswith($1S):
                    if $2S not in kwargs:
                        kwargs[$2S] = {}
                    kwargs[$2S][key[$3L:]] = $4L

                """, locationName, memberName, locationName.length(), mapTarget.accept(deserVisitor));
        }
    }

    /**
     * A section that controls deserializing HTTP fields, namely headers.
     *
     * <p>By default, it handles values based on smithy.api#httpHeader and
     * smithy.api#httpPrefixHeaders traits.
     *
     * @param operationOrError The operation or error whose fields section is being generated.
     */
    public record DeserializeFieldsSection(Shape operationOrError) implements CodeSection {}

    private void deserializeStatusCode(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeStatusCodeSection(operationOrError));
        var statusBinding = bindingIndex.getResponseBindings(operationOrError, Location.RESPONSE_CODE);
        if (!statusBinding.isEmpty()) {
            var statusMember = context.symbolProvider().toMemberName(statusBinding.get(0).getMember());
            writer.write("kwargs[$S] = http_response.status_code", statusMember);
        }
        writer.popState();
    }

    /**
     * A section that controls deserializing the HTTP status code.
     *
     * @param operationOrError The operation or error whose status code section is being generated.
     */
    public record DeserializeStatusCodeSection(Shape operationOrError) implements CodeSection {}

    private void deserializeBody(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        HttpBindingIndex bindingIndex
    ) {
        writer.pushState(new DeserializeBodySection(operationOrError));
        var documentBindings = bindingIndex.getResponseBindings(operationOrError, DOCUMENT);
        if (!documentBindings.isEmpty()) {
            deserializeDocumentBody(context, writer, operationOrError, documentBindings);
            for (HttpBinding binding : documentBindings) {
                var target = context.model().expectShape(binding.getMember().getTarget());
                deserializingDocumentShapes.add(target);
            }
        }

        var payloadBindings = bindingIndex.getResponseBindings(operationOrError, PAYLOAD);
        if (!payloadBindings.isEmpty()) {
            var binding = payloadBindings.get(0);
            deserializePayloadBody(context, writer, operationOrError, binding);
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
     * @param operationOrError The operation or error whose body section is being generated.
     */
    public record DeserializeBodySection(Shape operationOrError) implements CodeSection {}

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
     * @param operationOrError The operation or error whose output document is being deserialized.
     * @param documentBindings The bindings to read from the document.
     */
    protected abstract void deserializeDocumentBody(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
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
     * @param operationOrError The operation or error whose output payload is being deserialized.
     * @param binding The payload binding to deserialize.
     */
    protected void deserializePayloadBody(
        GenerationContext context,
        PythonWriter writer,
        Shape operationOrError,
        HttpBinding binding
    ) {
        // TODO: implement payload deserialization
        // This will have a default implementation since it'll mostly be standard
    }

    /**
     * Given context and a source of data, generate an input value provider for the
     * shape. This may use native types or invoke complex type serializers to
     * manipulate the dataSource into the proper input content.
     */
    private static class HttpMemberSerVisitor extends ShapeVisitor.Default<String> {
        private final GenerationContext context;
        private final PythonWriter writer;
        private final String dataSource;
        private final Location bindingType;
        private final MemberShape member;
        private final Format defaultTimestampFormat;

        /**
         * @param context The generation context.
         * @param writer The writer to add dependencies to.
         * @param bindingType How this value is bound to the operation input.
         * @param dataSource The in-code location of the data to provide an output of
         *                   ({@code input.foo}, {@code entry}, etc.)
         * @param member The member that points to the value being provided.
         * @param defaultTimestampFormat The default timestamp format to use.
         */
        HttpMemberSerVisitor(
            GenerationContext context,
            PythonWriter writer,
            Location bindingType,
            String dataSource,
            MemberShape member,
            Format defaultTimestampFormat
        ) {
            this.context = context;
            this.writer = writer;
            this.dataSource = dataSource;
            this.bindingType = bindingType;
            this.member = member;
            this.defaultTimestampFormat = defaultTimestampFormat;
        }

        @Override
        protected String getDefault(Shape shape) {
            var protocolName = context.protocolGenerator().getName();
            throw new CodegenException(String.format(
                "Unsupported %s binding of %s to %s in %s using the %s protocol",
                bindingType, member.getMemberName(), shape.getType(), member.getContainer(), protocolName));
        }

        @Override
        public String blobShape(BlobShape shape) {
            if (member.getMemberTrait(context.model(), StreamingTrait.class).isPresent()) {
                return dataSource;
            }
            writer.addStdlibImport("base64", "b64encode");
            return format("b64encode(%s).decode('utf-8')", dataSource);
        }

        @Override
        public String booleanShape(BooleanShape shape) {
            return String.format("('true' if %s else 'false')", dataSource);
        }

        @Override
        public String stringShape(StringShape shape) {
            if (bindingType == Location.HEADER) {
                if (shape.hasTrait(MediaTypeTrait.class)) {
                    writer.addStdlibImport("base64", "b64encode");
                    return format("b64encode(%s.encode('utf-8')).decode('utf-8')", dataSource);
                }
            }
            return dataSource;
        }

        @Override
        public String byteShape(ByteShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String shortShape(ShortShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String integerShape(IntegerShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String longShape(LongShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String bigIntegerShape(BigIntegerShape shape) {
            return integerShape();
        }

        private String integerShape() {
            return String.format("str(%s)", dataSource);
        }

        @Override
        public String floatShape(FloatShape shape) {
            // TODO: use strict parsing
            return floatShapes();
        }

        @Override
        public String doubleShape(DoubleShape shape) {
            // TODO: use strict parsing
            return floatShapes();
        }

        @Override
        public String bigDecimalShape(BigDecimalShape shape) {
            return floatShapes();
        }

        private String floatShapes() {
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            writer.addImport("smithy_python.utils", "serialize_float");
            return String.format("serialize_float(%s)", dataSource);
        }

        @Override
        public String timestampShape(TimestampShape shape) {
            var httpIndex = HttpBindingIndex.of(context.model());
            var format = switch (bindingType) {
                case HEADER -> httpIndex.determineTimestampFormat(member, bindingType, Format.HTTP_DATE);
                case LABEL -> httpIndex.determineTimestampFormat(member, bindingType, defaultTimestampFormat);
                case QUERY -> httpIndex.determineTimestampFormat(member, bindingType, Format.DATE_TIME);
                default ->
                    throw new CodegenException("Unexpected named member shape binding location `" + bindingType + "`");
            };

            return HttpProtocolGeneratorUtils.getTimestampInputParam(
                context, writer, dataSource, member, format);
        }
    }

    /**
     * Given context and a source of data, generate an output value provider for the
     * shape. This may use native types (like generating a datetime for timestamps)
     * converters (like a b64decode) or invoke complex type deserializers to
     * manipulate the dataSource into the proper output content.
     */
    private static class HttpMemberDeserVisitor extends ShapeVisitor.Default<String> {

        private final GenerationContext context;
        private final PythonWriter writer;
        private final String dataSource;
        private final Location bindingType;
        private final MemberShape member;
        private final Format defaultTimestampFormat;

        /**
         * @param context The generation context.
         * @param writer The writer to add dependencies to.
         * @param bindingType How this value is bound to the operation output.
         * @param dataSource The in-code location of the data to provide an output of
         *                   ({@code output.foo}, {@code entry}, etc.)
         * @param member The member that points to the value being provided.
         * @param defaultTimestampFormat The default timestamp format to use.
         */
        HttpMemberDeserVisitor(
            GenerationContext context,
            PythonWriter writer,
            Location bindingType,
            String dataSource,
            MemberShape member,
            Format defaultTimestampFormat
        ) {
            this.context = context;
            this.writer = writer;
            this.dataSource = dataSource;
            this.bindingType = bindingType;
            this.member = member;
            this.defaultTimestampFormat = defaultTimestampFormat;
        }

        @Override
        protected String getDefault(Shape shape) {
            var protocolName = context.protocolGenerator().getName();
            throw new CodegenException(String.format(
                "Unsupported %s binding of %s to %s in %s using the %s protocol",
                bindingType, member.getMemberName(), shape.getType(), member.getContainer(), protocolName));
        }

        @Override
        public String blobShape(BlobShape shape) {
            if (bindingType == PAYLOAD) {
                return dataSource;
            }
            throw new CodegenException("Unexpected blob binding location `" + bindingType + "`");
        }

        @Override
        public String booleanShape(BooleanShape shape) {
            switch (bindingType) {
                case QUERY, LABEL, HEADER -> {
                    writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                    writer.addImport("smithy_python.utils", "strict_parse_bool");
                    return "strict_parse_bool(" + dataSource + ")";
                }
                default -> throw new CodegenException("Unexpected boolean binding location `" + bindingType + "`");
            }
        }

        @Override
        public String byteShape(ByteShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String shortShape(ShortShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String integerShape(IntegerShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String longShape(LongShape shape) {
            // TODO: perform bounds checks
            return integerShape();
        }

        @Override
        public String bigIntegerShape(BigIntegerShape shape) {
            return integerShape();
        }

        private String integerShape() {
            return switch (bindingType) {
                case QUERY, LABEL, HEADER, RESPONSE_CODE -> "int(" + dataSource + ")";
                default -> throw new CodegenException("Unexpected integer binding location `" + bindingType + "`");
            };
        }

        @Override
        public String floatShape(FloatShape shape) {
            // TODO: use strict parsing
            return floatShapes();
        }

        @Override
        public String doubleShape(DoubleShape shape) {
            // TODO: use strict parsing
            return floatShapes();
        }

        private String floatShapes() {
            switch (bindingType) {
                case QUERY, LABEL, HEADER -> {
                    writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                    writer.addImport("smithy_python.utils", "strict_parse_float");
                    return "strict_parse_float(" + dataSource + ")";
                }
                default -> throw new CodegenException("Unexpected float binding location `" + bindingType + "`");
            }
        }

        @Override
        public String bigDecimalShape(BigDecimalShape shape) {
            switch (bindingType) {
                case QUERY, LABEL, HEADER -> {
                    writer.addStdlibImport("decimal", "Decimal", "_Decimal");
                    return "_Decimal(" + dataSource + ")";
                }
                default -> throw new CodegenException("Unexpected bigDecimal binding location `" + bindingType + "`");
            }
        }

        @Override
        public String stringShape(StringShape shape) {
            if ((bindingType == HEADER || bindingType == PREFIX_HEADERS) && shape.hasTrait(MediaTypeTrait.ID)) {
                writer.addStdlibImport("base64", "b64decode");
                return  "b64decode(" + dataSource + ").decode('utf-8')";
            }

            return dataSource;
        }

        @Override
        public String timestampShape(TimestampShape shape) {
            HttpBindingIndex httpIndex = HttpBindingIndex.of(context.model());
            Format format = httpIndex.determineTimestampFormat(member, bindingType, defaultTimestampFormat);
            var source = dataSource;
            if (format == Format.EPOCH_SECONDS) {
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python.utils", "strict_parse_float");
                source = "strict_parse_float(" + dataSource + ")";
            }
            return HttpProtocolGeneratorUtils.getTimestampOutputParam(writer, source, member, format);
        }

        @Override
        public String listShape(ListShape shape) {
            if (bindingType != HEADER) {
                throw new CodegenException("Unexpected list binding location `" + bindingType + "`");
            }
            var collectionTarget = context.model().expectShape(shape.getMember().getTarget());
            writer.addImport("smithy_python.httputils", "split_header");
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            String split = String.format("split_header(%s or '')", dataSource);;

            // Headers that have HTTP_DATE formatted timestamps may not be quoted, so we need
            // to enable special handling for them.
            if (isHttpDate(shape.getMember(), collectionTarget)) {
                split = String.format("split_header(%s or '', True)", dataSource);
            }

            var targetDeserVisitor = new HttpMemberDeserVisitor(
                context, writer, bindingType, "e.strip()", shape.getMember(), defaultTimestampFormat);
            return String.format("[%s for e in %s]", collectionTarget.accept(targetDeserVisitor), split);
        }

        private boolean isHttpDate(MemberShape member, Shape target) {
            if (target.isTimestampShape()) {
                HttpBindingIndex httpIndex = HttpBindingIndex.of(context.model());
                Format format = httpIndex.determineTimestampFormat(member, bindingType, Format.HTTP_DATE);
                return format == Format.HTTP_DATE;
            }
            return false;
        }
    }
}
