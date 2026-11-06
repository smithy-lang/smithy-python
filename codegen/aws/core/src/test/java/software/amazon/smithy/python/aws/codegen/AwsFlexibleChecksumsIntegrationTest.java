/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.aws.traits.HttpChecksumTrait;
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
                operations: [GetData, PutData, ListData]
            }

            service WithResponseChecksums {
                version: "2024-01-01"
                operations: [GetData]
            }

            service WithRequestChecksums {
                version: "2024-01-01"
                operations: [PutData]
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

            @httpChecksum(requestAlgorithmMember: "algorithm")
            operation PutData {
                input := {
                    algorithm: Algorithm
                }
            }

            enum Algorithm {
                CRC32
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

    private static List<HttpChecksumTrait> traits(String service) {
        var model = model();
        return AwsFlexibleChecksumsIntegration.checksumTraits(
                model,
                model.expectShape(ShapeId.from("smithy.example#" + service), ServiceShape.class));
    }

    private static boolean hasRequest(String service) {
        return traits(service).stream().anyMatch(AwsFlexibleChecksumsIntegration::hasRequestChecksum);
    }

    private static boolean hasResponse(String service) {
        return traits(service).stream().anyMatch(AwsFlexibleChecksumsIntegration::hasResponseChecksum);
    }

    @Test
    public void testDetectsBothSides() {
        assertTrue(hasRequest("WithChecksums"));
        assertTrue(hasResponse("WithChecksums"));
    }

    @Test
    public void testDetectsOnlyResponseChecksums() {
        assertFalse(hasRequest("WithResponseChecksums"));
        assertTrue(hasResponse("WithResponseChecksums"));
    }

    @Test
    public void testDetectsOnlyRequestChecksums() {
        assertTrue(hasRequest("WithRequestChecksums"));
        assertFalse(hasResponse("WithRequestChecksums"));
    }

    @Test
    public void testIgnoresServiceWithoutHttpChecksumOperation() {
        assertTrue(traits("WithoutChecksums").isEmpty());
    }
}
