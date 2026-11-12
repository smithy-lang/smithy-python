/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import software.amazon.smithy.build.MockManifest;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.TitleTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSettings.ArtifactType;
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

    @Test
    public void defaultDescriptionUsesServiceTitle() {
        // Without an explicit moduleDescription, the pyproject.toml description should be
        // derived from the standard smithy.api#title trait, while the README keeps its
        // legacy "<module> client" description.
        assertDescription(
                service("smithy.example#DynamoDB", "Amazon DynamoDB"),
                null,
                ArtifactType.CLIENT,
                "Python client for Amazon DynamoDB",
                "test_client client");
    }

    static Stream<Arguments> packageDescriptionCases() {
        var titled = service("smithy.example#Weather", "Example Weather Service");
        var untitled = service("smithy.example#Weather", null);
        var client = ArtifactType.CLIENT;
        var types = ArtifactType.TYPES;
        var titledDefault = "Python client for Example Weather Service";
        return Stream.of(
                Arguments.of("explicit",
                        titled,
                        "Custom description",
                        client,
                        "Custom description",
                        "Custom description"),
                Arguments.of("explicit old default",
                        titled,
                        "test_client client",
                        client,
                        "test_client client",
                        "test_client client"),
                Arguments.of("blank", titled, "   ", client, titledDefault, "test_client client"),
                Arguments.of("titled", titled, null, client, titledDefault, "test_client client"),
                Arguments.of("untitled", untitled, null, client, "Python client for Weather", "test_client client"),
                Arguments.of("types default", titled, null, types, "test_client types", "test_client types"),
                Arguments.of("types explicit", titled, "Custom types", types, "Custom types", "Custom types"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("packageDescriptionCases")
    public void resolvesPackageDescription(
            String name,
            ServiceShape service,
            String moduleDescription,
            ArtifactType artifactType,
            String expectedPyproject,
            String expectedLegacy
    ) {
        assertDescription(service, moduleDescription, artifactType, expectedPyproject, expectedLegacy);
    }

    private static ServiceShape service(String id, String title) {
        var builder = ServiceShape.builder().id(id).version("2024-01-01");
        if (title != null) {
            builder.addTrait(new TitleTrait(title));
        }
        return builder.build();
    }

    private static void assertDescription(
            ServiceShape service,
            String moduleDescription,
            ArtifactType artifactType,
            String expectedPyproject,
            String expectedLegacy
    ) {
        var model = Model.builder().addShape(service).build();
        var settings = PythonSettings.builder()
                .service(service.getId())
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .moduleDescription(moduleDescription)
                .artifactType(artifactType)
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
        String pyproject = manifest.expectFileString("pyproject.toml");
        String readme = manifest.expectFileString("README.md");

        // pyproject.toml uses the model-aware description, while the README and the
        // no-argument accessor keep their legacy "<module> <artifact type>" default.
        assertAll(
                () -> assertTrue(pyproject.contains("description = \"" + expectedPyproject + "\"\n"), pyproject),
                () -> assertTrue(readme.contains("\n" + expectedLegacy + "\n"), readme),
                () -> assertEquals(expectedLegacy, settings.moduleDescription()));
    }
}
