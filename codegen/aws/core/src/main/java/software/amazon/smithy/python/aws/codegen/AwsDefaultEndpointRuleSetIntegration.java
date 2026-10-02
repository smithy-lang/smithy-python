/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.rulesengine.traits.EndpointRuleSetTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Stamps the default AWS regional endpoint ruleset onto an AWS service that has neither a ruleset
 * nor a BDD, so the core endpoint-bdd integration (which runs after this) can derive the BDD.
 * Non-AWS services are left for the core integration's manual-endpoint default.
 */
@SmithyInternalApi
public final class AwsDefaultEndpointRuleSetIntegration implements PythonIntegration {

    @Override
    public List<String> runBefore() {
        return List.of("endpoint-bdd");
    }

    @Override
    public Model preprocessModel(Model model, PythonSettings settings) {
        var service = settings.service(model);
        if (service.hasTrait(EndpointBddTrait.class)
                || service.hasTrait(EndpointRuleSetTrait.class)
                || !CodegenUtils.isAwsService(settings, model)) {
            return model;
        }

        var endpointPrefix = service.expectTrait(ServiceTrait.class).getEndpointPrefix();
        var ruleSet = EndpointRuleSetTrait.builder()
                .ruleSet(Node.parse(AWS_REGIONAL_RULE_SET.replace("ENDPOINT_PREFIX", endpointPrefix)))
                .build();

        return model.toBuilder()
                .removeShape(service.toShapeId())
                .addShape(service.toBuilder().addTrait(ruleSet).build())
                .build();
    }

    // Verbatim from aws-sdk-js-v3 AddDefaultAwsEndpointRuleSet.getDefaultRegionalEndpointRuleSet;
    // ENDPOINT_PREFIX is the service endpoint prefix.
    private static final String AWS_REGIONAL_RULE_SET =
            """
                    {
                      "version": "1.0",
                      "parameters": {
                        "Region": {
                          "builtIn": "AWS::Region",
                          "required": false,
                          "documentation": "The AWS Region. This is a default regional AWS endpointRuleSet.",
                          "type": "String"
                        },
                        "UseDualStack": {
                          "builtIn": "AWS::UseDualStack",
                          "required": true,
                          "default": false,
                          "documentation": "Whether to use dual-stack.",
                          "type": "Boolean"
                        },
                        "UseFIPS": {
                          "builtIn": "AWS::UseFIPS",
                          "required": true,
                          "default": false,
                          "documentation": "Whether to use FIPS-compliant regional endpoint.",
                          "type": "Boolean"
                        },
                        "Endpoint": {
                          "builtIn": "SDK::Endpoint",
                          "required": false,
                          "documentation": "Override the endpoint.",
                          "type": "String"
                        }
                      },
                      "rules": [
                        {
                          "conditions": [
                            {
                              "fn": "isSet",
                              "argv": [
                                {
                                  "ref": "Endpoint"
                                }
                              ]
                            }
                          ],
                          "rules": [
                            {
                              "conditions": [
                                {
                                  "fn": "booleanEquals",
                                  "argv": [
                                    {
                                      "ref": "UseFIPS"
                                    },
                                    true
                                  ]
                                }
                              ],
                              "error": "Invalid Configuration: FIPS and custom endpoint are not supported",
                              "type": "error"
                            },
                            {
                              "conditions": [
                                {
                                  "fn": "booleanEquals",
                                  "argv": [
                                    {
                                      "ref": "UseDualStack"
                                    },
                                    true
                                  ]
                                }
                              ],
                              "error": "Invalid Configuration: Dualstack and custom endpoint are not supported",
                              "type": "error"
                            },
                            {
                              "conditions": [],
                              "endpoint": {
                                "url": {
                                  "ref": "Endpoint"
                                },
                                "properties": {},
                                "headers": {}
                              },
                              "type": "endpoint"
                            }
                          ],
                          "type": "tree"
                        },
                        {
                          "conditions": [
                            {
                              "fn": "isSet",
                              "argv": [
                                {
                                  "ref": "Region"
                                }
                              ]
                            }
                          ],
                          "rules": [
                            {
                              "conditions": [
                                {
                                  "fn": "aws.partition",
                                  "argv": [
                                    {
                                      "ref": "Region"
                                    }
                                  ],
                                  "assign": "PartitionResult"
                                }
                              ],
                              "rules": [
                                {
                                  "conditions": [
                                    {
                                      "fn": "booleanEquals",
                                      "argv": [
                                        {
                                          "ref": "UseFIPS"
                                        },
                                        true
                                      ]
                                    },
                                    {
                                      "fn": "booleanEquals",
                                      "argv": [
                                        {
                                          "ref": "UseDualStack"
                                        },
                                        true
                                      ]
                                    }
                                  ],
                                  "rules": [
                                    {
                                      "conditions": [
                                        {
                                          "fn": "booleanEquals",
                                          "argv": [
                                            true,
                                            {
                                              "fn": "getAttr",
                                              "argv": [
                                                {
                                                  "ref": "PartitionResult"
                                                },
                                                "supportsFIPS"
                                              ]
                                            }
                                          ]
                                        },
                                        {
                                          "fn": "booleanEquals",
                                          "argv": [
                                            true,
                                            {
                                              "fn": "getAttr",
                                              "argv": [
                                                {
                                                  "ref": "PartitionResult"
                                                },
                                                "supportsDualStack"
                                              ]
                                            }
                                          ]
                                        }
                                      ],
                                      "rules": [
                                        {
                                          "conditions": [],
                                          "endpoint": {
                                            "url": "https://ENDPOINT_PREFIX-fips.{Region}.{PartitionResult#dualStackDnsSuffix}",
                                            "properties": {},
                                            "headers": {}
                                          },
                                          "type": "endpoint"
                                        }
                                      ],
                                      "type": "tree"
                                    },
                                    {
                                      "conditions": [],
                                      "error": "FIPS and DualStack are enabled, but this partition does not support one or both",
                                      "type": "error"
                                    }
                                  ],
                                  "type": "tree"
                                },
                                {
                                  "conditions": [
                                    {
                                      "fn": "booleanEquals",
                                      "argv": [
                                        {
                                          "ref": "UseFIPS"
                                        },
                                        true
                                      ]
                                    }
                                  ],
                                  "rules": [
                                    {
                                      "conditions": [
                                        {
                                          "fn": "booleanEquals",
                                          "argv": [
                                            {
                                              "fn": "getAttr",
                                              "argv": [
                                                {
                                                  "ref": "PartitionResult"
                                                },
                                                "supportsFIPS"
                                              ]
                                            },
                                            true
                                          ]
                                        }
                                      ],
                                      "rules": [
                                        {
                                          "conditions": [
                                            {
                                              "fn": "stringEquals",
                                              "argv": [
                                                {
                                                  "fn": "getAttr",
                                                  "argv": [
                                                    {
                                                      "ref": "PartitionResult"
                                                    },
                                                    "name"
                                                  ]
                                                },
                                                "aws-us-gov"
                                              ]
                                            }
                                          ],
                                          "endpoint": {
                                            "url": "https://ENDPOINT_PREFIX.{Region}.amazonaws.com",
                                            "properties": {},
                                            "headers": {}
                                          },
                                          "type": "endpoint"
                                        },
                                        {
                                          "conditions": [],
                                          "endpoint": {
                                            "url": "https://ENDPOINT_PREFIX-fips.{Region}.{PartitionResult#dnsSuffix}",
                                            "properties": {},
                                            "headers": {}
                                          },
                                          "type": "endpoint"
                                        }
                                      ],
                                      "type": "tree"
                                    },
                                    {
                                      "conditions": [],
                                      "error": "FIPS is enabled but this partition does not support FIPS",
                                      "type": "error"
                                    }
                                  ],
                                  "type": "tree"
                                },
                                {
                                  "conditions": [
                                    {
                                      "fn": "booleanEquals",
                                      "argv": [
                                        {
                                          "ref": "UseDualStack"
                                        },
                                        true
                                      ]
                                    }
                                  ],
                                  "rules": [
                                    {
                                      "conditions": [
                                        {
                                          "fn": "booleanEquals",
                                          "argv": [
                                            true,
                                            {
                                              "fn": "getAttr",
                                              "argv": [
                                                {
                                                  "ref": "PartitionResult"
                                                },
                                                "supportsDualStack"
                                              ]
                                            }
                                          ]
                                        }
                                      ],
                                      "rules": [
                                        {
                                          "conditions": [],
                                          "endpoint": {
                                            "url": "https://ENDPOINT_PREFIX.{Region}.{PartitionResult#dualStackDnsSuffix}",
                                            "properties": {},
                                            "headers": {}
                                          },
                                          "type": "endpoint"
                                        }
                                      ],
                                      "type": "tree"
                                    },
                                    {
                                      "conditions": [],
                                      "error": "DualStack is enabled but this partition does not support DualStack",
                                      "type": "error"
                                    }
                                  ],
                                  "type": "tree"
                                },
                                {
                                  "conditions": [],
                                  "endpoint": {
                                    "url": "https://ENDPOINT_PREFIX.{Region}.{PartitionResult#dnsSuffix}",
                                    "properties": {},
                                    "headers": {}
                                  },
                                  "type": "endpoint"
                                }
                              ],
                              "type": "tree"
                            }
                          ],
                          "type": "tree"
                        },
                        {
                          "conditions": [],
                          "error": "Invalid Configuration: Missing Region",
                          "type": "error"
                        }
                      ]
                    }
                    """;
}
