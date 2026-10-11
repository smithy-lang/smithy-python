/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.build.MockManifest;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSymbolProvider;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.writer.PythonDelegator;

public class SetupGeneratorTest {

    /**
     * When a client depends on smithy_http (the common case, since all transports default to aiohttp),
     * an {@code awscrt} extra is exposed that re-exports smithy_http's own awscrt extra so the version
     * constraint stays sourced from smithy-http.
     */
    @Test
    public void exposesAwscrtExtraForSmithyHttpDependency() {
        var smithyHttp = SmithyPythonDependency.SMITHY_HTTP.getDependency();
        Map<String, SymbolDependency> dependencies = Map.of(smithyHttp.getPackageName(), smithyHttp);

        var extras = SetupGenerator.collectOptionalDependencies(dependencies);

        assertEquals(
                Map.of("awscrt", List.of("smithy_http[awscrt]" + smithyHttp.getVersion())),
                extras);
    }

    @Test
    public void readmeKeepsRawTripleQuotesInCodeSpans() {
        // The README is Markdown, not a docstring, so the docstring quote escaping
        // must not show up there as literal backslashes.
        var service = ServiceShape.builder()
                .id("smithy.example#TestService")
                .version("2024-01-01")
                .addTrait(new DocumentationTrait("Use <code>\"\"\"</code> here."))
                .build();
        var model = Model.builder().addShape(service).build();
        var settings = PythonSettings.builder()
                .service(service.getId())
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
        var manifest = new MockManifest();
        var delegator = new PythonDelegator(manifest, new PythonSymbolProvider(model, settings), settings);
        var context = GenerationContext.builder()
                .model(model)
                .settings(settings)
                .fileManifest(manifest)
                .writerDelegator(delegator)
                .build();

        SetupGenerator.generateSetup(settings, context);
        delegator.flushWriters();
        String readme = manifest.expectFileString("README.md");

        assertTrue(readme.contains("Use `\"\"\"` here."), readme);
    }
}
