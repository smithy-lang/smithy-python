/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
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
        String packageName,
        String version,
        Type type,
        boolean isLink,
        List<String> optionalDependencies) implements SymbolDependencyContainer {

    public PythonDependency(
            String packageName,
            String version,
            Type type,
            boolean isLink
    ) {
        this(packageName, version, type, isLink, Collections.emptyList());
    }

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
                .putProperty(SymbolProperties.IS_LINK, isLink)
                .putProperty(SymbolProperties.OPTIONAL_DEPENDENCIES, optionalDependencies)
                .build();
    }

    public PythonDependency withOptionalDependencies(String... optionalDependencies) {
        return new PythonDependency(packageName, version, type, isLink, List.of(optionalDependencies));
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
