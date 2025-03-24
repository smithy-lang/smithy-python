/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A section that controls writing a union member.
 */
@SmithyInternalApi
public record UnionMemberSection(Symbol memberSymbol) implements CodeSection {}
