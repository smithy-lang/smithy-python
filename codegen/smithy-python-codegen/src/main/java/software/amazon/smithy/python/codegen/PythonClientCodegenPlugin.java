/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
        CodegenDirector<PythonWriter, PythonIntegration, GenerationContext, PythonSettings> runner
                = new CodegenDirector<>();

        PythonSettings settings = PythonSettings.from(context.getSettings());
        runner.settings(settings);
        runner.directedCodegen(new DirectedPythonCodegen());
        runner.fileManifest(context.getFileManifest());
        runner.service(settings.getService());
        runner.model(context.getModel());
        runner.integrationClass(PythonIntegration.class);
        runner.performDefaultCodegenTransforms();
        runner.createDedicatedInputsAndOutputs();
        runner.run();
    }
}
