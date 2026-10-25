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
        assertTrue(client.contains("(AsyncClient):"));
        assertTrue(client.contains("await self._prepare_call("));

        // Members named self and plugins are escaped. The body's locals avoid the
        // parameter names, and a parameter named locals means the arguments are
        // passed explicitly instead of through locals().
        var shadowedSignature = normalize("""
                async def shadowed_names(
                    self,
                    *,
                    pipeline: str | None = None,
                    call: str | None = None,
                    locals: str | None = None,
                    self_: str | None = None,
                    plugins_: str | None = None,
                    plugins: list[Plugin] | None = None,
                ) ->""");
        var normalizedClient = normalize(client);
        assertTrue(normalizedClient.contains(shadowedSignature), client);
        assertTrue(normalizedClient.contains(normalize("""
                pipeline_, call_ = await self._prepare_call(
                    {"pipeline": pipeline, "call": call, "locals": locals, "self_": self_, "plugins_": plugins_}
                """)), client);
        assertTrue(normalizedClient.contains(normalize("return await pipeline_(call_)")), client);

        // The stub declares the same signature, with the docs.
        var clientStub = Files.readString(tempDir.resolve("src/weather/client.pyi"));
        assertTrue(normalize(clientStub).contains(shadowedSignature), clientStub);

        // The dictionary forms: optional keys allow None, required keys are Required,
        // and a union is the alias of its single-key variant forms.
        var params = normalize(Files.readString(tempDir.resolve("src/weather/_params.pyi")));
        assertTrue(params.contains(normalize("""
                class ShadowedNamesInputParams(TypedDict, total=False):
                    pipeline: str | None
                    call: str | None
                    locals: str | None
                    self_: str | None
                    plugins_: str | None
                """)), params);
        assertTrue(params.contains(normalize("""
                class PNGImageParams(TypedDict, total=False):
                    height: Required[int]
                    width: Required[int]
                """)), params);
        assertTrue(params.contains(normalize("""
                class ImageTypeRawParams(TypedDict):
                    raw: bool
                """)), params);
        assertTrue(params.contains(normalize("ImageTypeParams = ImageTypeRawParams | ImageTypePngParams")),
                params);
        var paramsModule = Files.readString(tempDir.resolve("src/weather/_params.py"));
        assertTrue(paramsModule.contains("def __getattr__(name: str)"), paramsModule);

        // Response tests pass a placeholder for every required parameter.
        var protocolTests = Files.readString(tempDir.resolve("tests/test_restjson_protocol.py"));
        assertTrue(normalize(protocolTests).contains(normalize("""
                await client.required_parameters(
                    label="placeholder",
                    blob=b"placeholder",
                    yes_no="YES",
                    int_yes_no=1,
                    amount=Decimal("0"),
                    time=datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc),
                    document=Document(None),
                    names=[],
                    tags={},
                    image=PNGImage(height=0, width=0),
                    image_type=ImageTypeRaw(value=False),
                    chain=Chain(next=ChainLinkEnd(value="placeholder")),
                )""")), protocolTests);

        var config = Files.readString(tempDir.resolve("src/weather/config.py"));
        assertTrue(config.contains("self.transport = transport or AIOHTTPClient()"));
        assertFalse(config.contains("self.transport = transport or AWSCRTHTTPClient()"));

        // An output that models a "responseMetadata" member gets both the SDK-reserved
        // response_metadata attribute and the escaped modeled member, so neither shadows
        // the other. Field declarations live in the typed stub (models.py builds
        // classes lazily at runtime), so the surface is asserted against models.pyi.
        var models = Files.readString(tempDir.resolve("src/weather/models.pyi"));
        assertTrue(models.contains("response_metadata: ResponseMetadata"));
        assertTrue(models.contains("response_metadata_:"));

        // Event streams are passed through the stream API, not model constructors.
        var typecheck = Files.readString(tempDir.resolve("tests/_typecheck.py"));
        assertFalse(typecheck.contains("stream=_"));

        var schemas = Files.readString(tempDir.resolve("src/weather/_private/schemas.py"));
        assertTrue(schemas.contains("example.weather#fakeProtocol"));
        assertTrue(schemas.contains("aws.protocols#restJson1"));
        assertTrue(schemas.contains("smithy.api#httpApiKeyAuth"));
        assertTrue(schemas.contains("\"name\": \"weather-auth\""));
        assertTrue(schemas.contains("smithy.rules#endpointBdd"));
        assertTrue(schemas.contains("(default endpointRuleSet) endpoint is not set"));
        assertTrue(schemas.contains("smithy.api#longPoll"));
        assertTrue(schemas.contains("\"timeoutMillis\": 20000"));
    }

    // Generated files are formatted only if ruff is installed, so compare them without
    // whitespace or the trailing commas the formatter adds and removes.
    private static String normalize(String code) {
        return code.replaceAll("\\s+", "").replaceAll(",([)\\]}])", "$1");
    }
}
