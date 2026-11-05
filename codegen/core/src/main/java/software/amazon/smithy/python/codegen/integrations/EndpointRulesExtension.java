/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.Optional;
import java.util.function.Consumer;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Provides details for generating code that uses an endpoint rules extension.
 *
 * <p>The service's default endpoint resolver gets the extension, and generated endpoint
 * tests configure their clients for the built-ins it binds.
 */
@SmithyUnstableApi
public interface EndpointRulesExtension {

    /**
     * @param context The code generation context.
     * @return Returns the symbol of the {@code smithy_core.endpoints.RulesExtension}.
     */
    Symbol getRulesExtensionSymbol(GenerationContext context);

    /**
     * Writes the config entries every generated endpoint test sets, such as test
     * credentials, as {@code "field": value,} lines of a dict literal. A test case's own
     * entries replace them.
     *
     * @param context The code generation context.
     * @param writer The writer to write the entries with.
     */
    default void writeEndpointTestConfig(GenerationContext context, PythonWriter writer) {}

    /**
     * Gets the config entry that sets a built-in this extension binds in generated
     * endpoint tests, written as one {@code "field": value,} line of a dict literal.
     *
     * <p>Code generation itself sets {@code SDK::Endpoint} and built-ins that are also
     * client context parameters. A test case that sets any other built-in to a value
     * other than its default is skipped unless an extension sets it.
     *
     * @param context The code generation context.
     * @param builtIn The built-in, such as {@code AWS::Region}.
     * @param value The value the test case gives it.
     * @return Returns the entry's writer, or empty if this extension doesn't set the
     *     built-in.
     */
    default Optional<Consumer<PythonWriter>> getEndpointTestBuiltIn(
            GenerationContext context,
            String builtIn,
            Node value
    ) {
        return Optional.empty();
    }
}
