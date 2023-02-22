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

import static java.lang.String.format;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ToShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Generates code to implement a protocol for both servers and clients.
 */
@SmithyUnstableApi
public interface ProtocolGenerator {
    /**
     * Gets the supported protocol {@link ShapeId}.
     *
     * @return Returns the protocol supported
     */
    ShapeId getProtocol();

    /**
     * Gets the name of the protocol.
     *
     * <p>The default implementation is the ShapeId name of the protocol trait in
     * Smithy models (e.g., "aws.protocols#restJson1" would return "restJson1").
     *
     * @return Returns the protocol name.
     */
    default String getName() {
        return getProtocol().getName();
    }

    /**
     * Creates an application protocol for the generator.
     *
     * @return Returns the created application protocol.
     */
    ApplicationProtocol getApplicationProtocol();


    /**
     * Generates the name of a serializer function for shapes of a service that is not protocol-specific.
     *
     * @param context The code generation context.
     * @param shapeId The shape the serializer function is being generated for.
     * @return Returns the generated function name.
     */
    default String getSerializationFunctionName(GenerationContext context, ToShapeId shapeId) {
        var name = context.settings().getService(context.model()).getContextualName(shapeId);
        return "_serialize_" + CaseUtils.toSnakeCase(name);
    }

    /**
     * Generates the symbol for a serializer function for shapes of a service that is not protocol-specific.
     *
     * @param context The code generation context.
     * @param shapeId The shape the serializer function is being generated for.
     * @return Returns the generated symbol.
     */
    default Symbol getSerializationFunction(GenerationContext context, ToShapeId shapeId) {
        return Symbol.builder()
                .name(getSerializationFunctionName(context, shapeId))
                .namespace(format("%s.serialize", context.settings().getModuleName()), "")
                .definitionFile(format("./%s/serialize.py", context.settings().getModuleName()))
                .build();
    }

    /**
     * Generates the name of a deserializer function for shapes of a service that is not protocol-specific.
     *
     * @param context The code generation context.
     * @param shapeId The shape the deserializer function is being generated for.
     * @return Returns the generated function name.
     */
    default String getDeserializationFunctionName(GenerationContext context, ToShapeId shapeId) {
        var name = context.settings().getService(context.model()).getContextualName(shapeId);
        return "_deserialize_" + CaseUtils.toSnakeCase(name);
    }

    /**
     * Generates the symbol for a deserializer function for shapes of a service that is not protocol-specific.
     *
     * @param context The code generation context.
     * @param shapeId The shape the deserializer function is being generated for.
     * @return Returns the generated symbol.
     */
    default Symbol getDeserializationFunction(GenerationContext context, ToShapeId shapeId) {
        return Symbol.builder()
                .name(getDeserializationFunctionName(context, shapeId))
                .namespace(format("%s.deserialize", context.settings().getModuleName()), "")
                .definitionFile(format("./%s/deserialize.py", context.settings().getModuleName()))
                .build();
    }

    /**
     * Generates the symbol for the error deserializer function for an shape of a service that is not
     * protocol-specific.
     *
     * @param context The code generation context.
     * @param shapeId The shape id of the shape the error deserializer function is being generated for.
     * @return Returns the generated symbol.
     */
    default Symbol getErrorDeserializationFunction(GenerationContext context, ToShapeId shapeId) {
        var name = context.settings().getService(context.model()).getContextualName(shapeId);
        return Symbol.builder()
            .name("_deserialize_error_" + CaseUtils.toSnakeCase(name))
            .namespace(format("%s.deserialize", context.settings().getModuleName()), "")
            .definitionFile(format("./%s/deserialize.py", context.settings().getModuleName()))
            .build();
    }

    /**
     * Generates any standard code for service request/response serde.
     *
     * @param context Serde context.
     */
    default void generateSharedSerializerComponents(GenerationContext context) {
    }

    /**
     * Generates the code used to serialize the shapes of a service
     * for requests.
     *
     * @param context Serialization context.
     */
    void generateRequestSerializers(GenerationContext context);

    /**
     * Generates any standard code for service response deserialization.
     *
     * @param context Serde context.
     */
    default void generateSharedDeserializerComponents(GenerationContext context) {
    }

    /**
     * Generates the code used to deserialize the shapes of a service
     * for responses.
     *
     * @param context Deserialization context.
     */
    void generateResponseDeserializers(GenerationContext context);

    /**
     * Generates the code for validating the generated protocol's serializers and deserializers.
     *
     * @param context Generation context
     */
    default void generateProtocolTests(GenerationContext context) {
    }
}
