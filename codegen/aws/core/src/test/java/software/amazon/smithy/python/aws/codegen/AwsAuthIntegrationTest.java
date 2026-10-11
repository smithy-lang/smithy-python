/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.model.shapes.ServiceShape;

public class AwsAuthIntegrationTest {

    @ParameterizedTest
    @CsvSource({"s3, true", "sts, false", "s3-outposts, false"})
    public void testUsesS3SigningForS3SigningName(String signingName, boolean expected) {
        var service = ServiceShape.builder()
                .id("smithy.example#TestService")
                .version("2024-01-01")
                .addTrait(SigV4Trait.builder().name(signingName).build())
                .build();

        assertEquals(expected, AwsAuthIntegration.usesS3Signing(service));
    }

    @Test
    public void testDoesNotUseS3SigningWithoutSigV4() {
        var service = ServiceShape.builder()
                .id("smithy.example#TestService")
                .version("2024-01-01")
                .build();

        assertFalse(AwsAuthIntegration.usesS3Signing(service));
    }
}
