/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.util.Collection;
import java.util.Map;
import java.util.Optional;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.python.codegen.PythonDependency.Type;

/**
 * Generates package setup configuration files.
 */
final class SetupGenerator {

    private SetupGenerator() {}

    static void generateSetup(
            PythonSettings settings,
            PythonDelegator writers
    ) {
        var dependencies = SymbolDependency.gatherDependencies(writers.getDependencies().stream());
        writePyproject(settings, writers, dependencies);
        writeSetupCfg(settings, writers, dependencies);
    }

    /**
     * Write a pyproject.toml file.
     *
     * This file format is what the python ecosystem is trying to transition to
     * for package configuration. It allows for arbitrary build tools to share
     * configuration.
     */
    private static void writePyproject(
            PythonSettings settings,
            PythonDelegator writers,
            Map<String, Map<String, SymbolDependency>> dependencies
    ) {
        writers.useFileWriter("pyproject.toml", "", writer -> {
            writer.write("""
                    [build-system]
                    requires = ["setuptools", "wheel"]
                    build-backend = "setuptools.build_meta"

                    [project]
                    name = $S
                    version = $S
                    description = $S
                    requires-python = ">=3.8"
                    license = {text = "Apache-2.0"}
                    classifiers = [
                        "Development Status :: 2 - Pre-Alpha",
                        "Intended Audience :: Developers",
                        "Intended Audience :: System Administrators",
                        "Natural Language :: English",
                        "License :: OSI Approved :: Apache Software License",
                        "Programming Language :: Python",
                        "Programming Language :: Python :: 3",
                        "Programming Language :: Python :: 3 :: Only",
                        "Programming Language :: Python :: 3.8",
                        "Programming Language :: Python :: 3.9",
                        "Programming Language :: Python :: 3.10"
                    ]
                    """, settings.getModuleName(), settings.getModuleVersion(), settings.getModuleDescription());

            Optional.ofNullable(dependencies.get(Type.DEPENDENCY.getType())).ifPresent(deps -> {
                writer.openBlock("requires = [", "]", () -> writeDependencyList(writer, deps.values()));
            });

            Optional.ofNullable(dependencies.get(Type.TEST_DEPENDENCY.getType())).ifPresent(deps -> {
                writer.write("[project.optional-dependencies]");
                writer.openBlock("test = [", "]", () -> writeDependencyList(writer, deps.values()));
            });
        });
    }

    private static void writeDependencyList(PythonWriter writer, Collection<SymbolDependency> dependencies) {
        for (var iter = dependencies.iterator(); iter.hasNext();) {
            var dependency = iter.next();
            if (dependency.getProperty("isLink", Boolean.class).orElse(false)) {
                writer.writeInline("\"$L @ $L\"", dependency.getPackageName(), dependency.getVersion());
            } else {
                writer.writeInline("\"$L$L\"", dependency.getPackageName(), dependency.getVersion());
            }
            if (iter.hasNext()) {
                writer.write(",");
            } else {
                writer.write("");
            }
        }
    }

    /**
     * Write a setup.cfg file.
     *
     * This file is currently needed for setuptools while they work on PEP621
     * support (which defines the pyproject.toml config options). It is also
     * currently needed for a number of linting tools.
     */
    // TODO: remove most of this once setuptools supports PEP 621
    private static void writeSetupCfg(
            PythonSettings settings,
            PythonDelegator writers,
            Map<String, Map<String, SymbolDependency>> dependencies
    ) {
        writers.useFileWriter("setup.cfg", "", writer -> {
            writer.write("""
                    [flake8]
                    # We ignore E203, E501 for this project due to black
                    ignore = E203,E501

                    [pycodestyle]
                    # We ignore E203, E501 for this project due to black
                    ignore = E203,E501

                    [mypy]
                    strict = True
                    warn_unused_configs = True

                    [mypy-awscrt]
                    ignore_missing_imports = True

                    [mypy-pytest]
                    ignore_missing_imports = True

                    [metadata]
                    name = $L
                    version = $L
                    description = $L
                    license = Apache-2.0
                    python_requires = >=3.8
                    classifiers =
                        Development Status :: 2 - Pre-Alpha
                        Intended Audience :: Developers
                        Intended Audience :: System Administrators
                        Natural Language :: English
                        License :: OSI Approved :: Apache Software License
                        Programming Language :: Python
                        Programming Language :: Python :: 3
                        Programming Language :: Python :: 3 :: Only
                        Programming Language :: Python :: 3.8
                        Programming Language :: Python :: 3.9
                        Programming Language :: Python :: 3.10

                    [options.packages.find]
                    exclude = tests*

                    [options]
                    include_package_data = True
                    packages = find:
                    """, settings.getModuleName(), settings.getModuleVersion(), settings.getModuleDescription());

            Optional.ofNullable(dependencies.get(Type.DEPENDENCY.getType())).ifPresent(deps -> {
                writer.openBlock("install_requires =", "", () -> {
                    deps.values().forEach(dep -> {
                        if (dep.getProperty("isLink", Boolean.class).orElse(false)) {
                            writer.write("$L @ $L", dep.getPackageName(), dep.getVersion());
                        } else {
                            writer.write("$L$L", dep.getPackageName(), dep.getVersion());
                        }
                    });
                });
            });

            Optional.ofNullable(dependencies.get(Type.TEST_DEPENDENCY.getType())).ifPresent(deps -> {
                writer.write("[options.extras_require]");
                writer.openBlock("test =", "", () -> {
                    deps.values().forEach(dep -> writer.write("$L$L", dep.getPackageName(), dep.getVersion()));
                });
            });
        });
    }
}
