/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.build.SmithyBuildPlugin;
import software.amazon.smithy.codegen.core.directed.CodegenDirector;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;

/**
 * Plugin to trigger Python code generation.
 */
public final class PythonCodegenPlugin implements SmithyBuildPlugin {
    @Override
    public String getName() {
        return "python-codegen";
    }

    @Override
    public void execute(PluginContext context) {
        CodegenDirector<PythonWriter, PythonIntegration, GenerationContext, PythonSettings> runnner
                = new CodegenDirector<>();

        PythonSettings settings = PythonSettings.from(context.getSettings());
        runnner.settings(settings);
        runnner.directedCodegen(new DirectedPythonCodegen());
        runnner.fileManifest(context.getFileManifest());
        runnner.service(settings.getService());
        runnner.model(context.getModel());
        runnner.integrationClass(PythonIntegration.class);
        runnner.performDefaultCodegenTransforms();
        runnner.createDedicatedInputsAndOutputs();
        runnner.run();
    }
}
