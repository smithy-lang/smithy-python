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

    /**
     * The sync (urllib3) and async (aiohttp) default transports are opt-in through {@code sync}
     * and {@code async} mode extras rather than base requirements, while unrelated smithy_http
     * extras (here the cbor protocol extra) stay in the base requirement. The README shows how to
     * install them.
     */
    @Test
    public void movesDefaultTransportsIntoModeExtras() {
        var service = service("smithy.example#TestService", null);
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
        var smithyHttp = SmithyPythonDependency.SMITHY_HTTP;
        delegator.useFileWriter("test_client/client.py", "test_client.client", writer -> {
            writer.addDependency(smithyHttp.withOptionalDependencies("cbor"));
            writer.addDependency(smithyHttp.withOptionalDependencies("aiohttp"));
            writer.addDependency(smithyHttp.withOptionalDependencies("urllib3"));
            writer.addDependency(smithyHttp.withOptionalDependencies("aiohttp", "urllib3").asTestDependency());
        });

        SetupGenerator.generateSetup(settings, context);
        delegator.flushWriters();
        String pyproject = manifest.expectFileString("pyproject.toml");
        String readme = manifest.expectFileString("README.md");

        var version = smithyHttp.version();
        assertAll(
                () -> assertTrue(readme.contains("uv add \"test_client[sync,async]\""), readme),
                () -> assertTrue(readme.contains("pip install \"test_client[sync,async]\""), readme),
                () -> assertTrue(pyproject.contains("\"smithy_http[cbor]" + version + "\"\n]"), pyproject),
                () -> assertTrue(pyproject.contains("sync = [\n    \"smithy_http[urllib3]" + version + "\"\n]"),
                        pyproject),
                () -> assertTrue(pyproject.contains("async = [\n    \"smithy_http[aiohttp]" + version + "\"\n]"),
                        pyproject),
                () -> assertTrue(pyproject.contains("[dependency-groups]\ntest = [\n    \"smithy_http[aiohttp, urllib3]"
                        + version + "\"\n]"), pyproject));
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
