/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.Collections;
import java.util.List;
import software.amazon.smithy.codegen.core.SmithyIntegration;
import software.amazon.smithy.model.Model;
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
    default List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return Collections.emptyList();
    }

    /**
     * Supplies the resolution backend the generated config classes build on.
     *
     * <p>At most one integration may return a backend for a given service; the
     * core config generator uses it to choose the config base classes, extra
     * {@code resolve()} parameters, and extra {@code _FIELDS}. Returning empty
     * leaves the generic {@code smithy_core.config} backend in place.
     *
     * @param context The generation context.
     * @return The config backend, or empty to use the generic default.
     */
    default java.util.Optional<software.amazon.smithy.python.codegen.generators.ConfigBackend> configBackend(
            GenerationContext context
    ) {
        return java.util.Optional.empty();
    }

    default Model preprocessModel(Model model, PythonSettings settings) {
        return model;
    }

    /**
     * Writes out all extra files required by runtime plugins.
     */
    static void generatePluginFiles(GenerationContext context) {
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                if (runtimeClientPlugin.matchesService(context.model(), context.settings().service(context.model()))) {
                    runtimeClientPlugin.writeAdditionalFiles(context);
                }
            }
        }
    }
}
