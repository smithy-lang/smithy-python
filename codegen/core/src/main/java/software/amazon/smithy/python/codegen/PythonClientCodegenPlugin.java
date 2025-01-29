/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.build.SmithyBuildPlugin;
import software.amazon.smithy.codegen.core.directed.CodegenDirector;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Plugin to trigger Python code generation.
 */
@SmithyUnstableApi
public final class PythonClientCodegenPlugin implements SmithyBuildPlugin {
    @Override
    public String getName() {
        return "python-client-codegen";
    }

    @Override
    public void execute(PluginContext context) {
        CodegenDirector<PythonWriter, PythonIntegration, GenerationContext, PythonSettings> runner =
                new CodegenDirector<>();

        PythonSettings settings = PythonSettings.fromNode(context.getSettings());
        runner.settings(settings);
        runner.directedCodegen(new DirectedPythonClientCodegen());
        runner.fileManifest(context.getFileManifest());
        runner.service(settings.service());
        runner.model(context.getModel());
        runner.integrationClass(PythonIntegration.class);
        runner.performDefaultCodegenTransforms();
        runner.createDedicatedInputsAndOutputs();
        runner.run();
    }
}
