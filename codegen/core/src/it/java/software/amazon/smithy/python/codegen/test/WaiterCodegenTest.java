/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;
import software.amazon.smithy.waiters.WaitableTrait;

/**
 * Generates the waiters of a small client and checks their names, documentation,
 * runtime calls, and typing, offline.
 */
public class WaiterCodegenTest {

    private static final String MODEL = """
            $version: "2.0"
            namespace example.waits
            use aws.protocols#restJson1
            use smithy.waiters#waitable
            @restJson1
            service Waits { version: "1", operations: [GetThing, WaitUntilThingReady] }
            @readonly
            @waitable(
                ThingReady: {
                    documentation: "Waits until the thing is ready."
                    minDelay: 3
                    maxDelay: 30
                    acceptors: [
                        {
                            state: "success"
                            matcher: { output: { path: "status", expected: "READY", comparator: "stringEquals" } }
                        }
                    ]
                }
                ThingGone: {
                    deprecated: true
                    acceptors: [{ state: "success", matcher: { errorType: "NotFound" } }]
                }
            )
            @http(method: "POST", uri: "/thing")
            operation GetThing {
                input := { id: String, maxWaitTime: Integer }
                output := { status: String }
                errors: [NotFound]
            }
            @http(method: "POST", uri: "/wait")
            operation WaitUntilThingReady {}
            @error("client")
            structure NotFound {}
            """;
    private static final ShapeId GET_THING = ShapeId.from("example.waits#GetThing");

    // A waiter named like an operation's method gets an underscore. The operation
    // keeps its name, and an input member named like a waiter option is escaped.
    @Test
    public void generatesWaiters(@TempDir Path tempDir) throws Exception {
        generate(loadModel(), tempDir);
        var sync = Files.readString(tempDir.resolve("src/waits/client.py"));
        var async = Files.readString(tempDir.resolve("src/waits/aio/client.py"));
        assertTrue(sync.contains("from smithy_core.waiters import wait\n")
                && sync.contains("        return wait(\n")
                && sync.contains("    def wait_until_thing_ready_(\n")
                && sync.contains("    def wait_until_thing_ready(\n")
                && sync.contains("    def wait_until_thing_gone(\n")
                && sync.contains("            \"ThingReady\",\n")
                && sync.contains("Waits until the thing is ready.")
                && sync.contains("the waiter's 3.")
                && sync.contains("This waiter is deprecated."), sync);
        assertTrue(async.contains("from smithy_core.aio.waiters import wait_async\n")
                && async.contains("        return await wait_async(\n")
                && async.contains("    async def wait_until_thing_ready_(\n"), async);
        var schemas = Files.readString(tempDir.resolve("src/waits/_private/schemas.py"));
        assertTrue(schemas.contains("smithy.waiters#waitable"), schemas);

        Files.writeString(tempDir.resolve("src/waits_consumer.py"), """
                # pyright: reportUnnecessaryTypeIgnoreComment=true
                from typing import assert_type

                from waits import AsyncWaits, Waits
                from waits.models import GetThingOutput, WaitUntilThingReadyOutput


                def use(client: Waits) -> None:
                    assert_type(client.wait_until_thing_ready(), WaitUntilThingReadyOutput)
                    assert_type(
                        client.wait_until_thing_ready_(id="t", max_wait_time=60),
                        GetThingOutput | None,
                    )
                    assert_type(
                        client.wait_until_thing_gone(
                            {"id": "t", "max_wait_time_": 1},
                            max_wait_time=1.5,
                            min_delay=0.5,
                            max_delay=1,
                        ),
                        GetThingOutput | None,
                    )
                    client.wait_until_thing_gone(id="t")  # pyright: ignore


                async def use_async(client: AsyncWaits) -> None:
                    assert_type(
                        await client.wait_until_thing_gone(id="t", max_wait_time=1),
                        GetThingOutput | None,
                    )
                """);
        assertSucceeds(tempDir,
                "python3",
                "-m",
                "pyright",
                "src/waits_consumer.py",
                "src/waits/client.py",
                "src/waits/aio/client.py");
    }

    // A model built without validation can hold delays the runtime would reject.
    @Test
    public void rejectsMinDelayAboveMaxDelay(@TempDir Path tempDir) {
        var model = loadModel();
        var operation = model.expectShape(GET_THING, OperationShape.class);
        var trait = operation.expectTrait(WaitableTrait.class);
        var waiter = trait.getWaiters().get("ThingReady").toBuilder().minDelay(40).build();
        var changed = model.toBuilder()
                .addShape(operation.toBuilder()
                        .addTrait(trait.toBuilder().put("ThingReady", waiter).build())
                        .build())
                .build();
        var error = assertThrows(CodegenException.class, () -> generate(changed, tempDir));
        var message = String.valueOf(error.getMessage());
        assertTrue(message.contains("ThingReady") && message.contains(GET_THING.toString())
                && message.contains("minDelay of 40"), message);
    }

    private static Model loadModel() {
        var loader = WaiterCodegenTest.class.getClassLoader();
        return Model.assembler(loader)
                .discoverModels(loader)
                .addUnparsedModel("waits.smithy", MODEL)
                .assemble()
                .unwrap();
    }

    private static void generate(Model model, Path directory) {
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(directory))
                .settings(ObjectNode.builder()
                        .withMember("service", "example.waits#Waits")
                        .withMember("module", "waits")
                        .withMember("moduleVersion", "0.0.1")
                        .build())
                .model(model)
                .build();
        new PythonClientCodegenPlugin().execute(context);
    }

    private static void assertSucceeds(Path directory, String... command) throws Exception {
        var process = new ProcessBuilder(command)
                .directory(directory.toFile())
                .redirectErrorStream(true)
                .start();
        var output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertTrue(process.waitFor(300, TimeUnit.SECONDS), String.join(" ", command) + " timed out");
        System.out.println(output);
        assertEquals(0, process.exitValue(), output);
    }
}
