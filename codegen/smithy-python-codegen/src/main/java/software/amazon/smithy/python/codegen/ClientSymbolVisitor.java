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

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;

/**
 * Responsible for mapping service shapes to their client types.
 */
final class ClientSymbolVisitor extends SymbolVisitor {
    ClientSymbolVisitor(Model model, PythonSettings settings) {
        super(model, settings);
    }

    @Override
    public Symbol operationShape(OperationShape shape) {
        // TODO: implement operations
        return createStdlibSymbol(shape, "Any", "typing");
    }

    @Override
    public Symbol serviceShape(ServiceShape shape) {
        // TODO: implement clients
        return createStdlibSymbol(shape, "Any", "typing");
    }
}
