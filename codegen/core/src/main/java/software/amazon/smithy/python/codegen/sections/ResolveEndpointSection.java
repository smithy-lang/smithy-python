/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * This section resolves the service's endpoint and adds it to the transport
 * request, if necessary.
 *
 * <p>This is implemented by default only for HTTP protocols.
 */
@SmithyUnstableApi
public record ResolveEndpointSection() implements CodeSection {}
