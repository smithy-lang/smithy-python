/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.Map;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;

/**
 * Marks the known long-polling operations so the generic client generator
 * applies long-polling retry behavior to them.
 *
 * <p>These operations are hard-coded until the {@code aws.api#longPoll} trait
 * ships in service models. Once it ships, this can check for the trait instead.
 */
public final class AwsLongPollingIntegration implements PythonIntegration {

    private static final Map<String, Set<String>> LONG_POLLING_OPERATIONS = Map.of(
            "SQS",
            Set.of("ReceiveMessage"),
            "SFN",
            Set.of("GetActivityTask"),
            "SWF",
            Set.of("PollForActivityTask", "PollForDecisionTask"));

    @Override
    public boolean isLongPollingOperation(Model model, ServiceShape service, OperationShape operation) {
        return service.getTrait(ServiceTrait.class)
                .map(trait -> LONG_POLLING_OPERATIONS.get(trait.getSdkId()))
                .map(operations -> operations.contains(operation.getId().getName()))
                .orElse(false);
    }
}
