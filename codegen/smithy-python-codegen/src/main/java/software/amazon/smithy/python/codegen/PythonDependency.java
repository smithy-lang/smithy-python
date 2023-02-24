/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import java.util.Collections;
import java.util.List;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.codegen.core.SymbolDependencyContainer;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * A record of a python package dependency.
 */
@SmithyUnstableApi
public record PythonDependency(
        String packageName, String version, Type type, boolean isLink
) implements SymbolDependencyContainer {

    @Override
    public List<SymbolDependency> getDependencies() {
        return Collections.singletonList(getDependency());
    }

    /**
     * @return the SymbolDependency representation of this dependency.
     */
    public SymbolDependency getDependency() {
        return SymbolDependency.builder()
                .dependencyType(type.getType())
                .packageName(packageName)
                .version(version)
                .putProperty("isLink", isLink)
                .build();
    }

    /**
     * An enum of valid dependency types.
     */
    public enum Type {
        /** A normal dependency. */
        DEPENDENCY("dependency"),

        /** A dependency only used for testing purposes. */
        TEST_DEPENDENCY("testDependency");

        private final String type;

        Type(String type) {
            this.type = type;
        }

        /**
         * @return the string representation of the dependency type.
         */
        public String getType() {
            return type;
        }
    }
}
