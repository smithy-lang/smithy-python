/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.IntEnumShape;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A section that controls writing an integer enum.
 */
@SmithyInternalApi
public record IntEnumSection(IntEnumShape intEnumShape, Symbol enumSymbol) implements CodeSection {}
