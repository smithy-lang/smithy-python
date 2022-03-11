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

import static java.lang.String.format;

import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
final class ServerSymbolVisitor extends SymbolVisitor {

    private static final Logger LOGGER = Logger.getLogger(ServerSymbolVisitor.class.getName());

    ServerSymbolVisitor(Model model, PythonSettings settings) {
        super(model, settings);
    }

    @Override
    public Symbol serviceShape(ServiceShape shape) {
        String name = getDefaultShapeName(shape);
        return createSymbolBuilder(shape, name, format("%s.service", settings.getModuleName()))
                .definitionFile(format("./%s/service.py", settings.getModuleName()))
                .build();
    }

    @Override
    public Symbol operationShape(OperationShape shape) {
        String name = getDefaultShapeName(shape);

        String errorsName = name + "Errors";
        Symbol errors = createSymbolBuilder(shape, errorsName, format("%s.service", settings.getModuleName()))
                .definitionFile(format("./%s/service.py", settings.getModuleName()))
                .build();

        String serializerName = name + "Serializer";
        Symbol serializer = createSymbolBuilder(shape, serializerName, format("%s.service", settings.getModuleName()))
                .definitionFile(format("./%s/service.py", settings.getModuleName()))
                .build();

        return createSymbolBuilder(shape, name, format("%s.service", settings.getModuleName()))
                .definitionFile(format("./%s/service.py", settings.getModuleName()))
                .putProperty("errors", errors)
                .putProperty("serializer", serializer)
                .build();
    }
}
