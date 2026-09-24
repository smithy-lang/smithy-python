/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * A field of the module-level {@code _PROTOCOL_SETTINGS} bag.
 */
@SmithyUnstableApi
public enum ProtocolSettingsField {
    NAMESPACE,
    SERVICE_TARGET,
    VERSION
}
