/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen.integration;

import java.util.Collections;
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.DerivedProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Provides details for generating auth for an auth trait.
 */
@SmithyUnstableApi
public interface AuthScheme {

    /**
     * @return Returns the auth trait this scheme implements.
     */
    ShapeId getAuthTrait();

    /**
     * Gets the application protocol for the auth scheme.
     *
     * <p>The auth scheme will only be generated if its application protocol matches
     * that of the service protocol.
     *
     * @return Returns the created application protocol.
     */
    ApplicationProtocol getApplicationProtocol();

    /**
     * Gets a list of properties needed from config or input to authenticate requests.
     *
     * @return Returns a list of properties to gather for auth.
     */
    default List<DerivedProperty> getAuthProperties() {
        return Collections.emptyList();
    }

    /**
     * Gets a function that returns a potential auth option for a request.
     *
     * <p>This function will be given an object containing all the properties
     * defined by {@code getAuthProperties}.
     *
     * @param context The code generation context.
     * @return Returns a symbol referencing the auth option function.
     */
    Symbol getAuthOptionGenerator(GenerationContext context);

    /**
     * @param context The code generation context.
     * @return Returns the symbol for the auth scheme implementation.
     */
    Symbol getAuthSchemeSymbol(GenerationContext context);
}
