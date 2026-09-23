/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.Set;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
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
    ApplicationProtocol getApplicationProtocol(GenerationContext context);

    void initializeProtocol(GenerationContext context, PythonWriter writer);

    /**
     * Declares the extra {@code _PROTOCOL_SETTINGS} fields this protocol's constructor reads.
     *
     * <p>The shared {@code _PROTOCOL_SETTINGS} bag is the union across every protocol
     * the service resolves, not just the default -- a runtime override to a non-default
     * protocol instantiates against the same bag, so its metadata must already be
     * present. {@code NAMESPACE} and {@code SERVICE_TARGET} are always staged; a
     * protocol returns here only the additional fields it needs (e.g. awsQuery needs
     * {@code VERSION}). The default is empty.
     *
     * @param context Generation context
     * @return The extra settings fields this protocol requires.
     */
    default Set<ProtocolSettingsField> requiredProtocolSettings(GenerationContext context) {
        return Set.of();
    }

    /**
     * Generates the code for validating the generated protocol's serializers and deserializers.
     *
     * @param context Generation context
     */
    default void generateProtocolTests(GenerationContext context) {}
}
