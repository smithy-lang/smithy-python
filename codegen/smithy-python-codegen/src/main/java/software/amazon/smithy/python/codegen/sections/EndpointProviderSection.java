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

package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.CodeSection;

/**
 * This section is responsible for generating an HTTP endpoint provider.
 *
 * <p>This section MUST contain generated classes implementing the provided symbols.
 * The generated class implementing the endpointProviderSymbol MUST be an
 * implementation of {@literal smithy_python.interfaces.http.EndpointProvider}
 *
 * <p>The default implementations of these symbols uses a static endpoint
 * provided by the customer in the configuration.
 *
 * @param endpointResolverSymbol The symbol representing the endpoint provider.
 * @param endpointParamsSymbol The symbol representing the parameter bag required by the endpoint provider.
 */
public record EndpointProviderSection(
        Symbol endpointResolverSymbol, Symbol endpointParamsSymbol) implements CodeSection {
}
