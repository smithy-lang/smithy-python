/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.EndpointTrait;
import software.amazon.smithy.python.codegen.PythonSettings;

public class AwsEndpointRulesIntegrationTest {

    private static final String NS = "smithy.example";

    @Test
    public void testRemovesS3ControlAccountIdHostPrefix() {
        var model = preprocess("S3 Control");

        assertFalse(hasEndpointTrait(model, "AccountIdOperation"));
        assertEquals("data.", hostPrefix(model, "StaticOperation"));
    }

    @Test
    public void testKeepsAccountIdHostPrefixOfOtherServices() {
        var model = preprocess("Weather");

        assertEquals("{AccountId}.", hostPrefix(model, "AccountIdOperation"));
        assertTrue(hasEndpointTrait(model, "StaticOperation"));
    }

    private static Model preprocess(String sdkId) {
        Model model = Model.assembler()
                .discoverModels(AwsEndpointRulesIntegrationTest.class.getClassLoader())
                .addUnparsedModel("test.smithy", """
                        $version: "2"
                        namespace smithy.example

                        use aws.api#service

                        @service(sdkId: "%s")
                        service TestService {
                            version: "2024-01-01"
                            operations: [AccountIdOperation, StaticOperation]
                        }

                        @endpoint(hostPrefix: "{AccountId}.")
                        operation AccountIdOperation {
                            input := {
                                @required
                                @hostLabel
                                AccountId: String
                            }
                        }

                        @endpoint(hostPrefix: "data.")
                        operation StaticOperation {}
                        """.formatted(sdkId))
                .assemble()
                .unwrap();
        PythonSettings settings = PythonSettings.builder()
                .service(ShapeId.from(NS + "#TestService"))
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
        return new AwsEndpointRulesIntegration().preprocessModel(model, settings);
    }

    private static boolean hasEndpointTrait(Model model, String operation) {
        return model.expectShape(ShapeId.from(NS + "#" + operation)).hasTrait(EndpointTrait.class);
    }

    private static String hostPrefix(Model model, String operation) {
        return model.expectShape(ShapeId.from(NS + "#" + operation))
                .expectTrait(EndpointTrait.class)
                .getHostPrefix()
                .toString();
    }
}
