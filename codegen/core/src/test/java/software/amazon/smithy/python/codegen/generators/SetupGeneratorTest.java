/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
import software.amazon.smithy.model.node.ObjectNode;
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
        var manifest = generateSetup();
        String readme = manifest.expectFileString("README.md");

        assertTrue(readme.contains("Use `\"\"\"` here."), readme);
    }

    @Test
    public void readmeKeepsBackslashesAndDollarSignsLiteral() {
        // Markdown code is verbatim, down to a backslash before the closing backtick,
        // so the backslash escaping of a Python string must not show up in the README
        // either. It is written with $L, where a dollar sign that was escaped for the
        // writer stays doubled. Outside code, Markdown may escape the dollar sign.
        var manifest = generateSetup();
        String readme = manifest.expectFileString("README.md");

        assertTrue(readme.contains("`D:\\Users\\%USERNAME%\\`"), readme);
        assertTrue(readme.contains("`$LATEST`"), readme);
        assertTrue(readme.contains("$5"), readme);
        assertFalse(readme.contains("$$"), readme);
    }

    @Test
    public void packageCarriesTheTypeMarker() {
        // Without py.typed in the package, type checkers ignore an installed
        // client's inline types and its model stub. The marker is an empty file.
        var manifest = generateSetup();

        assertEquals("", manifest.expectFileString("src/test_client/py.typed"));
    }

    private static MockManifest generateSetup() {
        var service = ServiceShape.builder()
                .id("smithy.example#TestService")
                .version("2024-01-01")
                .addTrait(new DocumentationTrait("Use <code>\"\"\"</code> here.\n\n"
                        + "A new `D:\\Users\\%USERNAME%\\` folder costs $5 for each `$LATEST` version."))
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

        try {
            SetupGenerator.generateSetup(settings, context);
        } finally {
            context.pandocWorker().close();
        }
        delegator.flushWriters();
        return manifest;
    }

    static Stream<Arguments> packageDescriptionCases() {
        var titled = service("smithy.example#Weather", "Example Weather Service");
        var untitled = service("smithy.example#Weather", null);
        var client = ArtifactType.CLIENT;
        var types = ArtifactType.TYPES;
        var titledDefault = "Python client for Example Weather Service";
        var titledTypesDefault = "Python types for Example Weather Service";
        return Stream.of(
                Arguments.of("explicit", titled, "Custom description", client, "Custom description"),
                Arguments.of("explicit old default", titled, "test_client client", client, "test_client client"),
                Arguments.of("blank", titled, "   ", client, titledDefault),
                Arguments.of("titled", titled, null, client, titledDefault),
                Arguments.of("untitled", untitled, null, client, "Python client for Weather"),
                Arguments.of("types default", titled, null, types, titledTypesDefault),
                Arguments.of("types untitled", untitled, null, types, "Python types for Weather"),
                Arguments.of("types blank", titled, "   ", types, titledTypesDefault),
                Arguments.of("types explicit", titled, "Custom types", types, "Custom types"),
                Arguments.of("types explicit old default", titled, "test_client types", types, "test_client types"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("packageDescriptionCases")
    public void resolvesPackageDescription(
            String name,
            ServiceShape service,
            String moduleDescription,
            ArtifactType artifactType,
            String expected
    ) {
        assertDescription(service, moduleDescription, artifactType, expected);
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
            String expected
    ) {
        var model = Model.builder().addShape(service).build();
        PythonSettings settings;
        if (artifactType == ArtifactType.CLIENT) {
            // Clients are configured through the plugin's settings parsing.
            var config = ObjectNode.builder()
                    .withMember("service", service.getId().toString())
                    .withMember("module", "test_client")
                    .withMember("moduleVersion", "0.0.1");
            if (moduleDescription != null) {
                config.withMember("moduleDescription", moduleDescription);
            }
            settings = PythonSettings.fromNode(config.build());
        } else {
            // The types plugin converts its own settings through the builder.
            settings = PythonSettings.builder()
                    .service(service.getId())
                    .moduleName("test_client")
                    .moduleVersion("0.0.1")
                    .moduleDescription(moduleDescription)
                    .artifactType(artifactType)
                    .build();
        }
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

        // Both generated files carry the same resolved description.
        assertAll(
                () -> assertTrue(pyproject.contains("description = \"" + expected + "\"\n"), pyproject),
                () -> assertTrue(readme.contains("\n" + expected + "\n"), readme));
    }
}
