/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * A field of the module-level {@code _PROTOCOL_SETTINGS} bag.
 *
 * <p>The bag is shared by the default protocol and any runtime override, so it must
 * carry the union of the metadata every protocol the service resolves could need -- a
 * consumer may override to a non-default protocol whose constructor reads a field the
 * default never touches. {@link #NAMESPACE} and {@link #SERVICE_TARGET} are always
 * present; the rest are opted into by whichever resolved protocol needs them.
 */
@SmithyUnstableApi
public enum ProtocolSettingsField {
    NAMESPACE,
    SERVICE_TARGET,
    VERSION
}
