/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;

public class CodegenUtilsTest {

    @Test
    public void testIsAwsServiceWithAwsServiceTrait() {
        // Create a mock context with an AWS service
        GenerationContext context = createMockContext(true);

        // Should return true for AWS services
        assertTrue(CodegenUtils.isAwsService(context));
    }

    @Test
    public void testIsAwsServiceWithoutAwsServiceTrait() {
        // Create a mock context with a non-AWS service
        GenerationContext context = createMockContext(false);

        // Should return false for non-AWS services
        assertFalse(CodegenUtils.isAwsService(context));
    }

    /**
     * Helper method to create a mock GenerationContext with a service shape.
     *
     * @param hasAwsServiceTrait whether the service has the AWS service trait
     * @return a mocked GenerationContext
     */
    private GenerationContext createMockContext(boolean hasAwsServiceTrait) {
        GenerationContext context = mock(GenerationContext.class);
        Model model = mock(Model.class);
        PythonSettings settings = mock(PythonSettings.class);

        ShapeId serviceId = ShapeId.from("test.service#TestService");
        ServiceShape serviceShape = mock(ServiceShape.class);

        when(context.model()).thenReturn(model);
        when(context.settings()).thenReturn(settings);
        when(settings.service()).thenReturn(serviceId);
        when(model.expectShape(serviceId)).thenReturn(serviceShape);
        when(serviceShape.hasTrait(software.amazon.smithy.aws.traits.ServiceTrait.class))
                .thenReturn(hasAwsServiceTrait);

        return context;
    }
}
