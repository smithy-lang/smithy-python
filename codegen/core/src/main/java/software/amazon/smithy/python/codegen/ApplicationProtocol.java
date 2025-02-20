/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Represents the resolves {@link Symbol}s and references for an
 * application protocol (e.g., "http", "mqtt", etc).
 */
@SmithyUnstableApi
public record ApplicationProtocol(
        String name,
        SymbolReference requestType,
        SymbolReference responseType,
        ObjectNode configuration) {
    /**
     * Checks if the protocol is an HTTP based protocol.
     *
     * @return Returns true if it is HTTP based.
     */
    public boolean isHttpProtocol() {
        return name.startsWith("http");
    }

    /**
     * Creates a default HTTP application protocol.
     *
     * @return Returns the created application protocol.
     */
    public static ApplicationProtocol createDefaultHttpApplicationProtocol(ObjectNode config) {
        return new ApplicationProtocol(
                "http",
                SymbolReference.builder()
                        .symbol(createHttpSymbol("HTTPRequest"))
                        .build(),
                SymbolReference.builder()
                        .symbol(createHttpSymbol("HTTPResponse"))
                        .build(),
                config);
    }

    /**
     * Creates a default HTTP application protocol.
     *
     * @return Returns the created application protocol.
     */
    public static ApplicationProtocol createDefaultHttpApplicationProtocol() {
        return createDefaultHttpApplicationProtocol(ObjectNode.objectNode());
    }

    private static Symbol createHttpSymbol(String symbolName) {
        PythonDependency dependency = SmithyPythonDependency.SMITHY_HTTP;
        return Symbol.builder()
                .namespace(dependency.packageName() + ".aio.interfaces", ".")
                .name(symbolName)
                .addDependency(dependency)
                .build();
    }
}
