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

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.model.traits.TitleTrait;
import software.amazon.smithy.python.codegen.PythonDependency.Type;
import software.amazon.smithy.python.codegen.sections.PyprojectSection;
import software.amazon.smithy.python.codegen.sections.ReadmeSection;
import software.amazon.smithy.utils.StringUtils;

/**
 * Generates package setup configuration files.
 */
final class SetupGenerator {

    private SetupGenerator() {}

    static void generateSetup(
            PythonSettings settings,
            GenerationContext context
    ) {
        var dependencies = SymbolDependency.gatherDependencies(context.writerDelegator().getDependencies().stream());
        writePyproject(settings, context.writerDelegator(), dependencies);
        writeReadme(settings, context);
    }

    /**
     * Write a pyproject.toml file.
     *
     * <p>This file format is what the python ecosystem is trying to transition to
     * for package configuration. It allows for arbitrary build tools to share
     * configuration.
     */
    private static void writePyproject(
            PythonSettings settings,
            WriterDelegator<PythonWriter> writers,
            Map<String, Map<String, SymbolDependency>> dependencies
    ) {
        // TODO: Allow all of these settings to be configured, particularly build system
        // The use of interceptors ostensibly allows this, but it would be better to have
        // a system that allows end users to configure it without writing code. Just
        // giving a generic JSON mapping would work since you can convert that to toml.
        // We can use the jsonAdd from Smithy's OpenAPI transforms for inspiration.
        writers.useFileWriter("pyproject.toml", "", writer -> {
            writer.pushState(new PyprojectSection(dependencies));
            writer.write("""
                    [build-system]
                    requires = ["setuptools", "setuptools-scm", "wheel"]
                    build-backend = "setuptools.build_meta"

                    [project]
                    name = $1S
                    version = $2S
                    description = $3S
                    readme = "README.md"
                    requires-python = ">=3.12"
                    keywords = ["smithy", $1S]
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
                        "Programming Language :: Python :: 3.12"
                    ]
                    """, settings.moduleName(), settings.moduleVersion(), settings.moduleDescription());

            Optional.ofNullable(dependencies.get(Type.DEPENDENCY.getType())).ifPresent(deps -> {
                writer.openBlock("dependencies = [", "]", () -> writeDependencyList(writer, deps.values()));
            });

            Optional.ofNullable(dependencies.get(Type.TEST_DEPENDENCY.getType())).ifPresent(deps -> {
                writer.write("[project.optional-dependencies]");
                writer.openBlock("tests = [", "]", () -> writeDependencyList(writer, deps.values()));
            });

            // TODO: remove the pyright global suppressions after the serde redo is done
            writer.write("""
                    [tool.setuptools.packages.find]
                    exclude=["tests*"]

                    [tool.pyright]
                    typeCheckingMode = "strict"
                    reportPrivateUsage = false
                    reportUnusedFunction = false
                    reportUnusedVariable = false
                    reportUnnecessaryComparison = false

                    [tool.black]
                    target-version = ["py311"]

                    [tool.pytest.ini_options]
                    python_classes = ["!Test"]
                    asyncio_mode = "auto"
                    """);

            writer.popState();
        });
    }

    private static void writeDependencyList(PythonWriter writer, Collection<SymbolDependency> dependencies) {
        for (var iter = dependencies.iterator(); iter.hasNext();) {
            writer.pushState();
            var dependency = iter.next();
            writer.putContext("deps", getOptionalDependencies(dependency));
            writer.putContext("isLink", dependency.getProperty(SymbolProperties.IS_LINK).orElse(false));
            writer.putContext("last", !iter.hasNext());
            writer.write("""
                    "$L\
                    ${?deps}[${#deps}${value:L}${^key.last}, ${/key.last}${/deps}]${/deps}\
                    ${?isLink} @ ${/isLink}$L"\
                    ${^last},${/last}""",
                    dependency.getPackageName(), dependency.getVersion());
            writer.popState();
        }
    }

    @SuppressWarnings("unchecked")
    private static List<String> getOptionalDependencies(SymbolDependency dependency) {
        var optionals = dependency.getProperty(SymbolProperties.OPTIONAL_DEPENDENCIES)
                .filter(list -> {
                    for (var d : list) {
                        if (!(d instanceof String)) {
                            return false;
                        }
                    }
                    return true;
                })
                .orElse(Collections.emptyList());
        try {
            return (List<String>) optionals;
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }

    private static void writeReadme(
            PythonSettings settings,
            GenerationContext context
    ) {
        var service = context.model().expectShape(settings.service());

        // see: https://smithy.io/2.0/spec/documentation-traits.html#smithy-api-title-trait
        var title = service.getTrait(TitleTrait.class)
                .map(StringTrait::getValue)
                .orElse(StringUtils.capitalize(settings.moduleName()));

        var description = StringUtils.isBlank(settings.moduleDescription())
                ? "Generated service client for " + title
                : StringUtils.wrap(settings.moduleDescription(), 80);

        context.writerDelegator().useFileWriter("README.md", writer -> {
            writer.pushState(new ReadmeSection());
            writer.write("""
                    ## $L Client

                    $L
                    """, title, description);

            service.getTrait(DocumentationTrait.class).map(StringTrait::getValue).ifPresent(documentation -> {
                // TODO: make sure this documentation is well-formed
                // Existing services in AWS, for example, have a lot of HTML docs.
                // HTML nodes *are* valid commonmark technically, so it should be
                // fine here. If we were to make this file RST formatted though,
                // we'd have a problem. We have to solve that at some point anyway
                // since the python code docs are RST format.
                writer.write("""
                        ### Documentation

                        $L
                        """, documentation);
            });
            writer.popState();
        });
    }
}
