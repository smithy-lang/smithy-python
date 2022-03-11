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

import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;

/**
 * Generates code for SSDK service classes.
 */
final class ServerGenerator implements Runnable {
    private final Model model;
    private final ServiceShape service;
    private final PythonWriter writer;
    private final SymbolProvider symbolProvider;

    ServerGenerator(Model model, ServiceShape service, PythonWriter writer, SymbolProvider symbolProvider) {
        this.model = model;
        this.service = service;
        this.writer = writer;
        this.symbolProvider = symbolProvider;
    }

    @Override
    public void run() {
    }
}
