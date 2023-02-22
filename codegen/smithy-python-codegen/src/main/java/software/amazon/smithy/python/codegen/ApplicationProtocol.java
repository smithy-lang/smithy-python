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

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Represents the resolves {@link Symbol}s and references for an
 * application protocol (e.g., "http", "mqtt", etc).
 */
@SmithyUnstableApi
public record ApplicationProtocol(String name, SymbolReference requestType, SymbolReference responseType) {

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
    public static ApplicationProtocol createDefaultHttpApplicationProtocol() {
        return new ApplicationProtocol(
                "http",
                SymbolReference.builder()
                        .symbol(createHttpSymbol("HTTPRequest"))
                        .build(),
                SymbolReference.builder()
                        .symbol(createHttpSymbol("HTTPResponse"))
                        .build()
        );
    }

    private static Symbol createHttpSymbol(String symbolName) {
        PythonDependency dependency = SmithyPythonDependency.SMITHY_PYTHON;
        return Symbol.builder()
                .namespace(dependency.packageName() + ".interfaces.http", ".")
                .name(symbolName)
                .addDependency(dependency)
                .build();
    }
}
