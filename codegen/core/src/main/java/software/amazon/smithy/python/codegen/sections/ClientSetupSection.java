/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.CodeSection;

/**
 * Section for the client's {@code _post_setup} override, which finishes lazy setup.
 *
 * <p>The section is empty by default, so clients without setup work inherit the
 * no-op; interceptors write the whole method.
 *
 * @param sync Whether the section is in the sync variant of the client.
 * @param config The config type the method accepts.
 */
public record ClientSetupSection(boolean sync, Symbol config) implements CodeSection {}
