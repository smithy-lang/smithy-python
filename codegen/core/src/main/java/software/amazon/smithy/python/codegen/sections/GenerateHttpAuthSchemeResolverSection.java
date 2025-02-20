/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.sections;

import java.util.List;
import software.amazon.smithy.python.codegen.integrations.AuthScheme;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A code section that controls generating the entire auth scheme resolver.
 *
 * @param authSchemes A list of supported auth schemes discovered on the path.
 */
@SmithyInternalApi
public record GenerateHttpAuthSchemeResolverSection(List<AuthScheme> authSchemes) implements CodeSection {}
