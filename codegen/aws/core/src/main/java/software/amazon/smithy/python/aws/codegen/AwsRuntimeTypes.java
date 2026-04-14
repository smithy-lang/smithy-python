/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Pre-defined Symbol constants for AWS-specific framework types used across generators.
 *
 * <p>Using these symbols with the {@code $T} formatter ensures that all framework type
 * references participate in the writer's collision detection system.
 */
@SmithyUnstableApi
public final class AwsRuntimeTypes {

    // smithy_aws_core.aio.protocols
    public static final Symbol REST_JSON_CLIENT_PROTOCOL = createSymbol(
            "aio.protocols",
            "RestJsonClientProtocol");
    public static final Symbol AWS_QUERY_CLIENT_PROTOCOL = createSymbol(
            "aio.protocols",
            "AwsQueryClientProtocol");

    // smithy_aws_core.identity
    public static final Symbol STATIC_CREDENTIALS_RESOLVER = createSymbol(
            "identity",
            "StaticCredentialsResolver");

    // smithy_aws_core.endpoints.standard_regional
    public static final Symbol STANDARD_REGIONAL_ENDPOINTS_RESOLVER = createSymbol(
            "endpoints.standard_regional",
            "StandardRegionalEndpointsResolver");

    private AwsRuntimeTypes() {}

    private static Symbol createSymbol(String module, String name) {
        var namespace = module.isEmpty() ? "smithy_aws_core" : "smithy_aws_core." + module;
        return Symbol.builder()
                .name(name)
                .namespace(namespace, ".")
                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                .build();
    }
}
