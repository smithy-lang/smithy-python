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

import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
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

    @Override
    public void generateRequestSerializers(GenerationContext context) {
        // TODO: Generate serializers for http bindings, e.g. non-body parts of the http request
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
                        raise NotImplementedError()
                    """, serFunction.getName(), inputSymbol, configSymbol, transportRequest);
            });
        }
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
                        raise NotImplementedError()
                    """, deserFunction.getName(), transportResponse, configSymbol, outputSymbol);
            });
        }
    }
}
