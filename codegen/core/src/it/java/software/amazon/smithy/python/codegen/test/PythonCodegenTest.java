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
        assertTrue(client.contains("_input = GetCurrentTimeInput()"));
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

        // Only `self` and `plugins` are reserved, and escaping is closed over trailing
        // underscores, so a member named `plugins_` keeps its own keyword.
        assertTrue(client.contains("plugins_: str | None = None"));
        assertTrue(client.contains("plugins__: str | None = None"));
        assertTrue(client.contains("plugins=plugins_,"));
        assertTrue(client.contains("plugins_=plugins__,"));
        assertTrue(client.contains("self=self_,"));

        // Python keywords are escaped once, by the symbol provider. The parameter escape
        // leaves the result alone rather than compounding on it.
        assertTrue(client.contains("class_: str | None = None"));
        assertTrue(client.contains("class_=class_,"));
        assertTrue(client.contains("from_=from_,"));
        assertTrue(client.contains("async_=async_,"));
        assertFalse(client.contains("class__"));

        // Only `self` and `plugins` are reserved. Members named after the locals the
        // operation body binds keep their own names, because those locals are underscored.
        assertTrue(client.contains("input: str | None = None"));
        assertTrue(client.contains("input=input,"));
        assertTrue(client.contains("config=config,"));
        assertTrue(client.contains("pipeline=pipeline,"));
        assertTrue(client.contains("call=call,"));
        assertTrue(client.contains("deepcopy=deepcopy,"));
        assertTrue(client.contains("retry_strategy=retry_strategy,"));
        assertTrue(client.contains("operation_plugins=operation_plugins,"));

        // Operation bodies bind only underscored locals, so members keep their own names
        // regardless of what the pipeline needs or which plugins matched the operation.
        assertTrue(client.contains("from copy import deepcopy as _deepcopy"));
        assertTrue(client.contains("_config = _deepcopy(self._config)"));
        assertTrue(client.contains("return await _pipeline(_call)"));
        assertTrue(client.contains("user_agent_plugin as _user_agent_plugin"));

        // Dataclass fields wrap the same default expressions in a factory callable.
        var models = Files.readString(tempDir.resolve("src/weather/models.py"));
        assertTrue(models.contains("input_list: list[UnionListMember] = field(default_factory=lambda: [])"));
        assertTrue(models.contains("document: Document = field(default_factory=lambda: Document(dict()))"));

        // `plugins` is documented by the same generator that documents members, so `Args:`
        // has content even for an input with no members. Undocumented members are left out
        // rather than given filler text.
        assertFalse(client.contains("Args:\n\n"));
        assertFalse(client.contains("input member."));

        var config = Files.readString(tempDir.resolve("src/weather/config.py"));
        assertTrue(config.contains("self.transport = transport or AIOHTTPClient()"));
        assertFalse(config.contains("self.transport = transport or AWSCRTHTTPClient()"));
    }
}
