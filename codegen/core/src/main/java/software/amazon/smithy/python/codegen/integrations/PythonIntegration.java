/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.Collections;
import java.util.List;
import software.amazon.smithy.codegen.core.SmithyIntegration;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.generators.ProtocolGenerator;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Java SPI for customizing Python code generation, registering
 * new protocol code generators, renaming shapes, modifying the model,
 * adding custom code, etc.
 */
@SmithyUnstableApi
public interface PythonIntegration extends SmithyIntegration<PythonSettings, PythonWriter, GenerationContext> {

    /**
     * Gets a list of protocol generators to register.
     *
     * @return Returns the list of protocol generators to register.
     */
    default List<ProtocolGenerator> getProtocolGenerators() {
        return Collections.emptyList();
    }

    /**
     * Gets a list of plugins to apply to the generated client.
     *
     * @return Returns the list of RuntimePlugins to apply to the client.
     */
    default List<RuntimeClientPlugin> getClientPlugins() {
        return Collections.emptyList();
    }
}
