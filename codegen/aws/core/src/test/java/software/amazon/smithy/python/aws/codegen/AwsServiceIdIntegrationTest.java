/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSymbolProvider;

public class AwsServiceIdIntegrationTest {

    private static final String NS = "smithy.example";

    @Test
    public void testFormerlyAliasedClientGetsAsyncNameWithoutAlias() {
        // "Bedrock Runtime" shipped under the unprefixed name and used to carry a
        // deprecated alias; it must now be Async-prefixed with no alias residue.
        var symbol = toServiceSymbol("Bedrock Runtime");

        assertEquals("AsyncBedrockRuntimeClient", symbol.getName());
        assertFalse(symbol.getTypedProperties().containsValue("BedrockRuntimeClient"));
    }

    @Test
    public void testNeverAliasedClientGetsAsyncNameWithoutAlias() {
        // "Weather" never shipped an unprefixed name; it must be Async-prefixed and,
        // like every other client, carry no alias.
        var symbol = toServiceSymbol("Weather");

        assertEquals("AsyncWeatherClient", symbol.getName());
        assertFalse(symbol.getTypedProperties().containsValue("WeatherClient"));
    }

    private static Symbol toServiceSymbol(String sdkId) {
        Model model = Model.assembler()
                .discoverModels(AwsServiceIdIntegrationTest.class.getClassLoader())
                .addUnparsedModel("test.smithy", """
                        $version: "2"
                        namespace smithy.example

                        use aws.api#service

                        @service(sdkId: "%s")
                        service TestService {
                            version: "2024-01-01"
                        }
                        """.formatted(sdkId))
                .assemble()
                .unwrap();
        PythonSettings settings = PythonSettings.builder()
                .service(ShapeId.from(NS + "#TestService"))
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
        var integration = new AwsServiceIdIntegration();
        var provider = integration.decorateSymbolProvider(model, settings, new PythonSymbolProvider(model, settings));
        return provider.toSymbol(model.expectShape(ShapeId.from(NS + "#TestService")));
    }
}
