/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

import java.util.ArrayList;

/**
 * A section that controls writing a union.
 */
@SmithyInternalApi
public record UnionSection(UnionShape unionShape, String parentName,
                           ArrayList<String> memberNames) implements CodeSection {
}
