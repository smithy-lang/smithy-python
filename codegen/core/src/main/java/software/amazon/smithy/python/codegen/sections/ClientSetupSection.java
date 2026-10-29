/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.utils.CodeSection;

/**
 * Section for service-specific lazy client setup.
 *
 * @param sync Whether the section is in the sync variant of the client.
 */
public record ClientSetupSection(boolean sync) implements CodeSection {
    public ClientSetupSection() {
        this(false);
    }
}
