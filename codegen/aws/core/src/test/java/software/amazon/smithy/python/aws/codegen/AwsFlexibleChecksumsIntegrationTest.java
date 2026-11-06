/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;

public class AwsFlexibleChecksumsIntegrationTest {

    private static final String MODEL = """
            $version: "2"
            namespace smithy.example

            use aws.protocols#httpChecksum

            service WithChecksums {
                version: "2024-01-01"
                operations: [GetData, ListData]
            }

            service WithoutChecksums {
                version: "2024-01-01"
                operations: [ListData]
            }

            @httpChecksum(requestValidationModeMember: "mode", responseAlgorithms: ["CRC32"])
            operation GetData {
                input := {
                    mode: ValidationMode
                }
            }

            enum ValidationMode {
                ENABLED
            }

            operation ListData {}
            """;

    private static Model model() {
        return Model.assembler()
                .discoverModels()
                .addUnparsedModel("test.smithy", MODEL)
                .assemble()
                .unwrap();
    }

    @Test
    public void testDetectsServiceWithHttpChecksumOperation() {
        var model = model();
        var service = model.expectShape(ShapeId.from("smithy.example#WithChecksums"), ServiceShape.class);

        assertTrue(AwsFlexibleChecksumsIntegration.hasHttpChecksumOperation(model, service));
    }

    @Test
    public void testIgnoresServiceWithoutHttpChecksumOperation() {
        var model = model();
        var service = model.expectShape(ShapeId.from("smithy.example#WithoutChecksums"), ServiceShape.class);

        assertFalse(AwsFlexibleChecksumsIntegration.hasHttpChecksumOperation(model, service));
    }
}
