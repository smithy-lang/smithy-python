/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Represents a property to be added to the generated client config object.
 *
 * @param name The name of the config field. This MUST be snake_cased.
 * @param type The type of the config field.
 * @param isOptional Whether the field is optional or not.
 * @param documentation Any relevant documentation for the config field.
 */
@SmithyUnstableApi
public record ConfigField(String name, Symbol type, boolean isOptional, String documentation) {
}
