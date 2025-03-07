/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import static software.amazon.smithy.python.codegen.types.CreateSyntheticService.SYNTHETIC_SERVICE_ID;

import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.build.SmithyBuildPlugin;
import software.amazon.smithy.codegen.core.directed.CodegenDirector;
import software.amazon.smithy.model.transform.ModelTransformer;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

public final class PythonTypeCodegenPlugin implements SmithyBuildPlugin {

    @Override
    public String getName() {
        return "python-type-codegen";
    }

    @Override
    public void execute(PluginContext context) {
        CodegenDirector<PythonWriter, PythonIntegration, GenerationContext, PythonSettings> runner =
                new CodegenDirector<>();

        var typeSettings = PythonTypeCodegenSettings.fromNode(context.getSettings());
        var service = typeSettings.service().orElse(SYNTHETIC_SERVICE_ID);
        var pythonSettings = typeSettings.toPythonSettings(service);

        var model = context.getModel();
        if (typeSettings.service().isEmpty()) {
            var transformer =
                    new CreateSyntheticService(typeSettings.selector(), typeSettings.generateInputsAndOutputs());
            model = transformer.transform(ModelTransformer.create(), model);
        }

        runner.settings(pythonSettings);
        runner.directedCodegen(new DirectedPythonTypeCodegen());
        runner.fileManifest(context.getFileManifest());
        runner.service(pythonSettings.service());
        runner.model(model);
        runner.integrationClass(PythonIntegration.class);
        runner.performDefaultCodegenTransforms();
        runner.run();
    }
}
