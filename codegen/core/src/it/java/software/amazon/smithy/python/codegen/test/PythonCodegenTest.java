/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.codegen.core.CodegenException;
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

        var client = Files.readString(tempDir.resolve("src/weather/aio/client.py"));
        assertTrue(client.contains("class AsyncWeather(AsyncClient[AsyncConfig]):"));
        assertTrue(client.contains("return AsyncConfig()"));
        assertFalse(client.contains("_post_setup"));
        assertTrue(client.contains("await self._invoke("));
        assertTrue(client.contains("from .. import models as _models"));
        assertTrue(client.contains("_models.GET_CITY,"));

        var config = Files.readString(tempDir.resolve("src/weather/aio/config.py"));
        assertTrue(config.contains("self.transport = transport or AIOHTTPClient()"));
        assertFalse(config.contains("self.transport = transport or AWSCRTHTTPClient()"));

        var syncClient = Files.readString(tempDir.resolve("src/weather/client.py"));
        assertTrue(syncClient.contains("class Weather(Client[Config]):"));
        assertTrue(syncClient.contains("return self._invoke("));
        // Sync operations carry the same docs as async ones.
        assertTrue(syncClient.contains("An instance of `GetCityOutput`."));

        // Each method of both clients has two overloads: one takes the whole request,
        // positional-only, as the input model or its dictionary form; the other takes
        // the modeled input members as keyword-only parameters. One implementation
        // takes either and hands them to _select_input.
        for (var generated : new String[] {client, syncClient}) {
            assertFalse(generated.contains("input: "));
            assertGenerated(generated, """
                        def get_city(
                            self,
                            request: _models.GetCityInput | _models.GetCityInputParams,
                            /,
                            *,
                            plugins: list[Plugin] | None = None,
                        ) -> GetCityOutput: ...
                    """);
            assertGenerated(generated, """
                        def get_city(
                            self,
                            /,
                            *,
                            city_id: str,
                            plugins: list[Plugin] | None = None,
                        ) -> GetCityOutput:
                    """);
            assertGenerated(generated, """
                        def get_city(
                            self,
                            /,
                            *args: object,
                            plugins: list[Plugin] | None = None,
                            **kwargs: object,
                        ) -> GetCityOutput:
                    """);
            assertGenerated(generated, """
                        self._invoke(
                            self._select_input(_models.GET_CITY, args, kwargs),
                            _models.GET_CITY,
                    """);
            // An operation without input members is called with no arguments.
            assertGenerated(generated, """
                        def get_current_time(
                            self,
                            /,
                            *,
                            plugins: list[Plugin] | None = None,
                        ) -> GetCurrentTimeOutput:
                    """);
            // Required members have no default; defaulted members and the idempotency
            // token may be omitted. Members named like the method's own parameters are
            // escaped, past a modeled member that already has the escaped name.
            assertGenerated(generated,
                    """
                                def create_connector(
                                    self,
                                    /,
                                    *,
                                    name: str,
                                    plugins__: Sequence[str],
                                    plugins_: str | None = None,
                                    self_: str | None = None,
                                    client_token: str | None = None,
                                    page_size: int | None = None,
                                    connector: _models.Connector | _models.Connector_Params | None = None,
                                    connectors: Sequence[_models.Connector | _models.Connector_Params] | None = None,
                                    sparse_connectors: Sequence[_models.Connector | _models.Connector_Params | None] | None = None,
                                    connectors_by_name: Mapping[str, _models.Connector | _models.Connector_Params] | None = None,
                                    image: _models.ImageType | _models.ImageTypeParams | None = None,
                                    recursive: _models.RecursiveUnion | _models.RecursiveUnionParams | None = None,
                                    mutual: _models.MutuallyRecursiveA | _models.MutuallyRecursiveAParams | None = None,
                                    connector_params: _models.ConnectorParams | _models.ConnectorParamsParams | None = None,
                                    settings: Document | None = None,
                                    kind: str | None = None,
                                    created_after: datetime | None = None,
                                    plugins: list[Plugin] | None = None,
                                ) -> CreateConnectorOutput:
                            """);
            // The members reach the runtime as the implementation's keyword arguments,
            // and the operation is resolved through the models module.
            assertGenerated(generated, """
                                self._select_input(_models.CREATE_CONNECTOR, args, kwargs),
                                _models.CREATE_CONNECTOR,
                    """);
            // Types used only in annotations are never imported at runtime.
            assertTrue(generated.contains("    from collections.abc import Mapping, Sequence\n"));
            assertTrue(generated.contains("    from datetime import datetime\n"));
            assertTrue(generated.contains("    from smithy_core.documents import Document\n"));
        }
        // The initial request of an event stream operation takes the same two forms;
        // the event stream member is sent through the returned stream.
        assertGenerated(client, """
                async def stream_atmospheric_conditions(
                    self,
                    request: _models.StreamAtmosphericConditionsInput
                        | _models.StreamAtmosphericConditionsInputParams,
                    /,
                    *,
                    plugins: list[Plugin] | None = None,
                ) -> AsyncDuplexEventStream[""");
        assertGenerated(client, """
                async def stream_atmospheric_conditions(
                    self,
                    /,
                    *,
                    city_id: str,
                    plugins: list[Plugin] | None = None,
                ) -> AsyncDuplexEventStream[""");
        assertGenerated(client, """
                async def stream_atmospheric_conditions(
                    self,
                    /,
                    *args: object,
                    plugins: list[Plugin] | None = None,
                    **kwargs: object,
                ) -> AsyncDuplexEventStream[""");
        assertGenerated(client, """
                pipeline, call = await self._prepare_call(
                    self._select_input(_models.STREAM_ATMOSPHERIC_CONDITIONS, args, kwargs),
                    _models.STREAM_ATMOSPHERIC_CONDITIONS,
                """);

        var aioInit = Files.readString(tempDir.resolve("src/weather/aio/__init__.py"));
        assertTrue(aioInit.contains("__all__ = [\"AsyncWeather\", \"AsyncConfig\"]"));
        var init = Files.readString(tempDir.resolve("src/weather/__init__.py"));
        assertTrue(init.contains("__all__ = [\"Weather\", \"Config\", \"AsyncWeather\", \"AsyncConfig\"]"));
        assertTrue(init.contains("\"AsyncWeather\": \".aio.client\""));

        // Async configs take either kind of endpoint resolver; sync ones take sync only.
        assertTrue(config.contains("endpoint_resolver: EndpointResolver | AsyncEndpointResolver"));

        var syncConfig = Files.readString(tempDir.resolve("src/weather/config.py"));
        assertTrue(syncConfig.contains("self.transport = transport or Urllib3HTTPClient()"));

        // An output that models a "responseMetadata" member gets both the SDK-reserved
        // response_metadata attribute and the escaped modeled member, so neither shadows
        // the other. Field declarations live in the typed stub (models.py builds
        // classes lazily at runtime), so the surface is asserted against models.pyi.
        var models = Files.readString(tempDir.resolve("src/weather/models.pyi"));
        assertTrue(models.contains("response_metadata: ResponseMetadata"));
        assertTrue(models.contains("response_metadata_:"));

        // Every structure reachable from an operation input has a TypedDict form whose
        // keys are the generated member names. Members that must be set are Required.
        assertGenerated(models, """
                class CreateConnectorInputParams(TypedDict, total=False):
                    ""\"Dictionary form of `CreateConnectorInput`.""\"
                    name: Required[str]
                    plugins__: Required[Sequence[str]]
                    plugins_: str | None
                    self_: str | None
                    client_token: str | None
                    ""\"This field is autopopulated if not provided.""\"
                    page_size: int | None
                    connector: Connector | Connector_Params | None
                """);
        // Members of nested structures are not parameters, so they are not escaped.
        // The plain name of Connector's dictionary form is taken by a modeled shape.
        assertGenerated(models, """
                class Connector_Params(TypedDict, total=False):
                    ""\"Dictionary form of `Connector`.""\"
                    name: Required[str]
                    version: int | None
                    plugins: Sequence[str] | None
                    image: ImageType | ImageTypeParams | None
                """);
        assertTrue(models.contains("class ConnectorParamsParams(TypedDict, total=False):"));
        // A union's dictionary form sets exactly one variant.
        assertGenerated(models, """
                class ImageTypeRawParams(TypedDict):
                    raw: bool

                class ImageTypePngParams(TypedDict):
                    png: PNGImage | PNGImageParams

                ImageTypeParams = Union[ImageTypeRawParams | ImageTypePngParams]
                """);
        // Recursive shapes refer to their own dictionary forms.
        assertGenerated(models, """
                class RecursiveUnionNestedParams(TypedDict):
                    nested: Mapping[str, RecursiveUnion | RecursiveUnionParams]
                """);
        assertTrue(models.contains("mutual: MutuallyRecursiveB | MutuallyRecursiveBParams | None"));
        // An input with a streaming body has two forms. The plain one takes the bodies
        // a sync client can send, so it unpacks into either client. The async one
        // also takes async streams, as the model and the async client do.
        assertTrue(models.contains("from smithy_core.aio.interfaces import StreamingBlob\n"));
        assertTrue(models.contains("from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob\n"));
        assertGenerated(models, """
                    name: Required[str]
                    image: Required[SyncStreamingBlob]

                class AsyncUploadCityImageInputParams(TypedDict, total=False):
                """);
        assertGenerated(models, """
                    name: Required[str]
                    image: Required[StreamingBlob]
                """);
        assertTrue(models.contains("class UploadCityImageInputParams(TypedDict, total=False):"));
        assertFalse(models.contains("AsyncCreateConnectorInputParams"));
        // Each client's method takes the body its mode can send.
        assertTrue(client.contains("    from smithy_core.aio.interfaces import StreamingBlob\n"));
        assertTrue(syncClient.contains("    from smithy_core.interfaces import StreamingBlob\n"));
        for (var generated : new String[] {client, syncClient}) {
            assertGenerated(generated, """
                        def upload_city_image(
                            self,
                            /,
                            *,
                            name: str,
                            image: StreamingBlob,
                            plugins: list[Plugin] | None = None,
                        ) -> UploadCityImageOutput:
                    """);
        }
        // The package is marked as typed, so the stub is used once it is installed.
        assertEquals("", Files.readString(tempDir.resolve("src/weather/py.typed")));

        // Dictionary forms are for input only: shapes that are only ever returned, and
        // events, have none.
        assertFalse(models.contains("class GetCityOutputParams"));
        assertFalse(models.contains("class CitySummaryParams"));
        assertFalse(models.contains("class HumiditySampleParams"));
        assertFalse(models.contains("AtmosphericConditionsParams"));

        var runtimeModels = Files.readString(tempDir.resolve("src/weather/models.py"));
        assertTrue(runtimeModels.contains("_operation_names = ("));
        assertTrue(runtimeModels.contains("_operation_data[\"GET_CITY\"]"));
        assertTrue(runtimeModels.contains("__all__.extend(_operation_names)"));
        assertTrue(runtimeModels.contains("return globals().setdefault(name, operation)"));
        assertFalse(runtimeModels.contains("GET_CITY = APIOperation("));

        // Event streams are passed through the stream API, not model constructors.
        var typecheck = Files.readString(tempDir.resolve("tests/_typecheck.py"));
        assertFalse(typecheck.contains("stream=_"));

        var schemas = readSchemaModules(tempDir.resolve("src/weather/_private"));
        assertTrue(schemas.contains("example.weather#fakeProtocol"));
        assertTrue(schemas.contains("aws.protocols#restJson1"));
        assertTrue(schemas.contains("smithy.api#httpApiKeyAuth"));
        assertTrue(schemas.contains("\"name\": \"weather-auth\""));
        // Lowering consumes the endpoint rules; the schemas no longer carry them.
        assertFalse(schemas.contains("smithy.rules#endpointBdd"));

        var endpoints = Files.readString(tempDir.resolve("src/weather/_private/endpoints.py"));
        assertTrue(endpoints.contains("(default endpointRuleSet) endpoint is not set"));
        assertTrue(config.contains(
                "self.endpoint_resolver = endpoint_resolver or BddEndpointResolver(BDD)"));
        assertTrue(config.contains("from .._private.endpoints import BDD"));
        assertTrue(syncConfig.contains("from ._private.endpoints import BDD"));
        assertTrue(schemas.contains("smithy.api#longPoll"));
        assertTrue(schemas.contains("\"timeoutMillis\": 20000"));
    }

    @Test
    public void partitionsLargeModels(@TempDir Path tempDir) throws IOException {
        var source = new StringBuilder("""
                $version: "2"
                namespace example.large

                use aws.protocols#restJson1

                @restJson1
                service Large {
                    version: "1",
                    operations: [GetLarge]
                }

                @http(method: "POST", uri: "/", code: 200)
                operation GetLarge {
                    input: GetLargeInput,
                    output: GetLargeOutput
                }

                @input
                structure GetLargeInput {
                    root: Shape0
                }

                @output
                structure GetLargeOutput {}

                """);
        for (int i = 0; i < 250; i++) {
            source.append("structure Shape")
                    .append(i)
                    .append(" { next: Shape")
                    .append(i + 1)
                    .append(" }\n");
        }
        source.append("structure Shape250 {}\n");

        var model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .addUnparsedModel("large.smithy", source.toString())
                .assemble()
                .unwrap();
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.large#Large")
                                .withMember("module", "large")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();

        // Pyright (seen with 1.1.406 and 1.1.414) overflows its stack on this synthetic
        // 251-deep chain of dictionary forms. Type checking is the last generation step,
        // so the generated files are still asserted before the test is aborted. Any
        // other failure, including any other pyright failure, still fails the test.
        var knownPyrightCrash = false;
        try {
            new PythonClientCodegenPlugin().execute(context);
        } catch (CodegenException e) {
            var message = e.getMessage();
            if (message == null
                    || !message.startsWith("Command `python3 -m pyright .` failed with output:")
                    || !message.contains("src/large/client.py\": RangeError: Maximum call stack size exceeded")) {
                throw e;
            }
            knownPyrightCrash = true;
        }

        var schemas = Files.readString(tempDir.resolve("src/large/_private/schemas.py"));
        assertTrue(schemas.contains("__all__ = list(_PARTITIONS)  # pyright: ignore[reportUnsupportedDunderAll]"));
        assertTrue(schemas.contains("\"SHAPE0\","));
        assertTrue(schemas.contains("\"SHAPE250\","));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/schemas_0.py")));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/schemas_1.py")));

        var models = Files.readString(tempDir.resolve("src/large/models.pyi"));
        assertTrue(models.contains("from ._private.models_0 import ("));
        assertTrue(models.contains("Shape0 as Shape0,"));
        assertTrue(models.contains("Shape250 as Shape250,"));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/models_0.pyi")));
        assertTrue(Files.exists(tempDir.resolve("src/large/_private/models_1.pyi")));

        // A shape's dictionary form is declared in its partition and re-exported with
        // it, so it is still imported from the public models module.
        assertTrue(models.contains("GetLargeInputParams as GetLargeInputParams,"));
        assertTrue(models.contains("Shape0Params as Shape0Params,"));
        assertTrue(models.contains("Shape250Params as Shape250Params,"));
        assertFalse(models.contains("class Shape0Params"));
        // Only shapes reachable from an operation input have one.
        assertFalse(models.contains("GetLargeOutputParams"));

        var partitions = readFiles(tempDir.resolve("src/large/_private"), "models_*.pyi");
        assertGenerated(partitions, "class GetLargeInputParams(TypedDict, total=False):");
        assertGenerated(partitions, "root: Shape0 | Shape0Params | None");
        assertGenerated(partitions, "class Shape250Params(TypedDict, total=False):");
        // A member refers to its target's model and dictionary form by their own
        // names, whether the target is declared in the same partition or another.
        for (int i = 0; i < 250; i++) {
            assertGenerated(partitions, String.format("next: Shape%1$d | Shape%1$dParams | None", i + 1));
        }
        assertFalse(partitions.contains(" as _Shape"));
        // The chain of shapes crosses the partition boundary, and the dictionary form
        // on the far side is imported through the public module, as its model is.
        assertTrue(Pattern.compile("from \\.\\.models import \\(?[^()]*?\\bShape\\d+Params\\b")
                .matcher(partitions)
                .find());

        // The client refers to both forms through the public models module.
        var client = Files.readString(tempDir.resolve("src/large/aio/client.py"));
        assertGenerated(client, "root: _models.Shape0 | _models.Shape0Params | None = None,");

        assumeTrue(!knownPyrightCrash,
                "Known Pyright limitation: type checking the synthetic 251-deep TypedDict chain hit"
                        + " RangeError: Maximum call stack size exceeded; generated-code assertions passed");
    }

    @Test
    public void keepsOperationSchemasTogether(@TempDir Path tempDir) throws IOException {
        var source = new StringBuilder("""
                $version: "2"
                namespace example.affinity

                use aws.protocols#restJson1

                @restJson1
                service Affinity {
                    version: "1",
                    operations: [
                """);
        var operationSuffixes = new ArrayList<String>();
        for (int i = 0; i < 60; i++) {
            operationSuffixes.add(i < 26
                    ? Character.toString((char) ('A' + i))
                    : Character.toString((char) ('A' + (i - 26) / 26))
                            + Character.toString((char) ('A' + (i - 26) % 26)));
        }
        for (var suffix : operationSuffixes) {
            source.append("Operation").append(suffix).append(",\n");
        }
        source.append("""
                    ]
                }

                """);
        for (var suffix : operationSuffixes) {
            source.append("@http(method: \"POST\", uri: \"/")
                    .append(suffix.toLowerCase())
                    .append("\", code: 200)\n")
                    .append("operation Operation")
                    .append(suffix)
                    .append(" { input: Operation")
                    .append(suffix)
                    .append("Input, output: Operation")
                    .append(suffix)
                    .append("Output }\n")
                    .append("@input structure Operation")
                    .append(suffix)
                    .append("Input {}\n")
                    .append("@output structure Operation")
                    .append(suffix)
                    .append("Output {}\n");
        }

        var model = Model.assembler(PythonCodegenTest.class.getClassLoader())
                .discoverModels(PythonCodegenTest.class.getClassLoader())
                .addUnparsedModel("affinity.smithy", source.toString())
                .assemble()
                .unwrap();
        var context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(
                        ObjectNode.builder()
                                .withMember("service", "example.affinity#Affinity")
                                .withMember("module", "affinity")
                                .withMember("moduleVersion", "0.0.1")
                                .build())
                .model(model)
                .build();

        new PythonClientCodegenPlugin().execute(context);

        var schemaDirectory = tempDir.resolve("src/affinity/_private");
        for (var suffix : operationSuffixes) {
            var operationName = "OPERATION_" + suffix;
            assertSchemaDeclarationsShareModule(
                    schemaDirectory,
                    operationName + ": StaticOperationSchema",
                    operationName + "_INPUT: StaticSchema",
                    operationName + "_OUTPUT: StaticSchema");
        }
    }

    private static String readSchemaModules(Path directory) throws IOException {
        return readFiles(directory, "schemas*.py");
    }

    private static String readFiles(Path directory, String glob) throws IOException {
        var result = new StringBuilder();
        try (var files = Files.newDirectoryStream(directory, glob)) {
            for (var file : files) {
                result.append(Files.readString(file));
            }
        }
        return result.toString();
    }

    private static void assertSchemaDeclarationsShareModule(Path directory, String... declarations) throws IOException {
        try (var files = Files.newDirectoryStream(directory, "schemas_*.py")) {
            for (var file : files) {
                var source = Files.readString(file);
                if (source.contains(declarations[0])) {
                    for (var declaration : declarations) {
                        assertTrue(source.contains(declaration));
                    }
                    return;
                }
            }
        }
        throw new AssertionError("No schema partition contained " + declarations[0]);
    }

    // Compares ignoring layout, so the assertions hold whether or not a formatter
    // was available to the generator.
    private static void assertGenerated(String generated, String expected) {
        assertTrue(compact(generated).contains(compact(expected)), () -> "missing from generated code:\n" + expected);
    }

    private static String compact(String code) {
        return code.replaceAll("\\s+", "").replace(",)", ")").replace(",]", "]").replace(",}", "}");
    }
}
