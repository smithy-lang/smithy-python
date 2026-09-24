/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

/**
 * Simple test that executes the Python client codegen plugin. Currently, this is about as much "testing" as
 * we can do, aside from the protocol tests. JUnit will set up and tear down a tempdir to house the codegen artifacts.
 */
public class PythonCodegenTest {

    @Test
    public void testCodegen(@TempDir Path tempDir) throws IOException {
        // TODO: Move this to its own package once client codegen is in its own package
        PythonClientCodegenPlugin plugin = new PythonClientCodegenPlugin();
        Model model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.weather#Weather")
                                .withMember("module", "weather")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();
        plugin.execute(context);

        var client = Files.readString(tempDir.resolve("src/weather/client.py"));
        assertFalse(client.contains("retry_mode="));
        assertFalse(client.contains("max_attempts="));
        assertTrue(client.contains("async def close(self) -> None:"));
        assertTrue(client.contains("if self._closed:"));

        // Ordinary, empty, and streaming operations all construct inputs from keywords.
        assertFalse(client.contains("input: GetCityInput"));
        assertTrue(client.contains("city_id: str | None = None"));
        assertTrue(client.contains("input = GetCurrentTimeInput()"));
        assertFalse(client.contains("input: StreamAtmosphericConditionsInput"));
        assertFalse(client.contains("stream: AtmosphericConditions"));
        assertTrue(client.contains("async def test_union_list_operation(\n        self,\n        *,"));
        assertTrue(client.contains("The values supplied by the caller."));

        // Mutable defaults are created inside the method, only when omitted. They're
        // declared `| None` rather than with a sentinel, so no private type leaks into
        // the public signature.
        assertTrue(client.contains("input_list: list[UnionListMember] | None = None"));
        assertFalse(client.contains("_Default.UNSET"));
        assertFalse(client.contains("class _Default"));
        assertTrue(client.contains("""
                        if input_list is None:
                            input_list = []
                """));
        assertTrue(client.contains("""
                        if document is None:
                            document = Document(dict())
                """));
        assertTrue(client.contains("input_list=input_list"));
        assertTrue(client.contains("document=document"));

        // SDK controls and colliding model members remain separate.
        assertTrue(client.contains("plugins__: str | None = None"));
        assertTrue(client.contains("plugins=plugins__"));
        assertTrue(client.contains("plugins_=plugins_"));
        assertTrue(client.contains("self=self_"));

        // Dataclass fields wrap the same default expressions in a factory callable.
        var models = Files.readString(tempDir.resolve("src/weather/models.py"));
        assertTrue(models.contains("input_list: list[UnionListMember] = field(default_factory=lambda: [])"));
        assertTrue(models.contains("document: Document = field(default_factory=lambda: Document(dict()))"));

        var config = Files.readString(tempDir.resolve("src/weather/config.py"));
        assertTrue(config.contains("self.transport = transport or AIOHTTPClient()"));
        assertFalse(config.contains("self.transport = transport or AWSCRTHTTPClient()"));
    }
}
