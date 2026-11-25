/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.HttpBearerAuthTrait;

public class AwsIdentityIntegrationTest {

    private static ServiceShape.Builder service() {
        return ServiceShape.builder()
                .id("smithy.example#TestService")
                .version("2024-01-01");
    }

    private static ServiceTrait awsService() {
        return ServiceTrait.builder()
                .sdkId("Test")
                .build(ShapeId.from("smithy.example#TestService"));
    }

    @Test
    public void testAppliesToAwsServicesWithSigV4() {
        var shape = service()
                .addTrait(awsService())
                .addTrait(SigV4Trait.builder().name("test").build())
                .build();

        assertTrue(AwsIdentityIntegration.appliesTo(shape));
    }

    @Test
    public void testAppliesToAwsServicesWithBearerAuth() {
        var shape = service()
                .addTrait(awsService())
                .addTrait(new HttpBearerAuthTrait())
                .build();

        assertTrue(AwsIdentityIntegration.appliesTo(shape));
    }

    @Test
    public void testSkipsAwsServicesWithoutIdentityAuth() {
        assertFalse(AwsIdentityIntegration.appliesTo(service().addTrait(awsService()).build()));
    }

    @Test
    public void testSkipsBearerAuthOutsideAws() {
        // The token chain reads an AWS config, which a service outside AWS lacks, so
        // its generated config keeps the static token resolver.
        var shape = service().addTrait(new HttpBearerAuthTrait()).build();

        assertFalse(AwsIdentityIntegration.appliesTo(shape));
    }
}
