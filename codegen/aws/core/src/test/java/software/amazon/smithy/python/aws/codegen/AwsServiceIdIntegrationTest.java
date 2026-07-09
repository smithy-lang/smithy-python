/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSymbolProvider;
import software.amazon.smithy.python.codegen.SymbolProperties;

public class AwsServiceIdIntegrationTest {

    private static final String NS = "smithy.example";

    @Test
    public void testServiceSymbolUsesAsyncClientNameWithDeprecatedAlias() {
        Model model = Model.assembler()
                .discoverModels(AwsServiceIdIntegrationTest.class.getClassLoader())
                .addUnparsedModel("test.smithy", """
                        $version: "2"
                        namespace smithy.example

                        use aws.api#service

                        @service(sdkId: "Bedrock Runtime")
                        service TestService {
                            version: "2024-01-01"
                        }
                        """)
                .assemble()
                .unwrap();
        PythonSettings settings = PythonSettings.builder()
                .service(ShapeId.from(NS + "#TestService"))
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
        var integration = new AwsServiceIdIntegration();
        var provider = integration.decorateSymbolProvider(model, settings, new PythonSymbolProvider(model, settings));

        var symbol = provider.toSymbol(model.expectShape(ShapeId.from(NS + "#TestService")));

        assertEquals("AsyncBedrockRuntimeClient", symbol.getName());
        assertEquals("BedrockRuntimeClient", symbol.expectProperty(SymbolProperties.DEPRECATED_ALIAS));
    }
}
