/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.rulesengine.traits.EndpointRuleSetTrait;
import software.amazon.smithy.rulesengine.transforms.CompileBdd;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Guarantees the service carries an {@link EndpointBddTrait} so endpoint resolution has a single
 * runtime representation. The BDD is derived from the ruleset if present, otherwise from a default
 * manual-endpoint-required ruleset. AWS services receive a regional default ruleset from an
 * aws/core integration that runs first, so by this point they already have a ruleset.
 */
@SmithyInternalApi
public final class EndpointBddIntegration implements PythonIntegration {

    @Override
    public String name() {
        return "endpoint-bdd";
    }

    @Override
    public Model preprocessModel(Model model, PythonSettings settings) {
        var service = settings.service(model);
        if (service.hasTrait(EndpointBddTrait.class)) {
            return model;
        }

        var ruleSetTrait = service.getTrait(EndpointRuleSetTrait.class)
                .orElseGet(() -> EndpointRuleSetTrait.builder()
                        .ruleSet(Node.parse(MANUAL_ENDPOINT_RULE_SET))
                        .build());
        var bdd = CompileBdd.compileBdd(ruleSetTrait.getEndpointRuleSet());

        return model.toBuilder()
                .removeShape(service.toShapeId())
                .addShape(service.toBuilder().addTrait(bdd).build())
                .build();
    }

    // Verbatim from smithy-typescript AddDefaultEndpointRuleSet.DEFAULT_RULESET.
    private static final String MANUAL_ENDPOINT_RULE_SET =
            """
                    {
                      "version": "1.0",
                      "parameters": {
                        "endpoint": {
                          "type": "string",
                          "builtIn": "SDK::Endpoint",
                          "documentation": "Endpoint used for making requests. Should be formatted as a URI."
                        }
                      },
                      "rules": [
                        {
                          "conditions": [
                            {
                              "fn": "isSet",
                              "argv": [
                                {
                                  "ref": "endpoint"
                                }
                              ]
                            }
                          ],
                          "endpoint": {
                            "url": {
                              "ref": "endpoint"
                            }
                          },
                          "type": "endpoint"
                        },
                        {
                          "conditions": [],
                          "error": "(default endpointRuleSet) endpoint is not set - you must configure an endpoint.",
                          "type": "error"
                        }
                      ]
                    }
                    """;
}
