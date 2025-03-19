/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.function.BinaryOperator;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.SymbolDependency;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.model.traits.TitleTrait;
import software.amazon.smithy.python.codegen.*;
import software.amazon.smithy.python.codegen.sections.PyprojectSection;
import software.amazon.smithy.python.codegen.sections.ReadmeSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;
import software.amazon.smithy.utils.StringUtils;

/**
 * Generates package setup configuration files.
 */
@SmithyInternalApi
public final class SetupGenerator {

    private SetupGenerator() {}

    public static void generateSetup(
            PythonSettings settings,
            GenerationContext context
    ) {
        writeDocsSkeleton(settings, context);
        var dependencies = gatherDependencies(context.writerDelegator().getDependencies().stream());
        writePyproject(settings, context.writerDelegator(), dependencies);
        writeReadme(settings, context);
    }

    /**
     * Merge all the symbol dependencies.  Also merges optional dependencies.
     * Modification of : SymbolDependency.gatherDependencies that also considers the OPTIONAL_DEPENDENCIES
     * property.
     */
    @SuppressWarnings("unchecked")
    private static Map<String, Map<String, SymbolDependency>> gatherDependencies(
            Stream<SymbolDependency> symbolStream
    ) {
        BinaryOperator<SymbolDependency> guardedMergeWithProperties = (a, b) -> {
            if (!a.getVersion().equals(b.getVersion())) {
                throw new CodegenException(String.format(
                        "Found a conflicting `%s` dependency for `%s`: `%s` conflicts with `%s`",
                        a.getDependencyType(),
                        a.getPackageName(),
                        a.getVersion(),
                        b.getVersion()));
            }
            // For our purposes, we need only consider OPTIONAL_DEPENDENCIES property.
            // The only other property currently used is IS_LINK, and it is consistent across all usages of
            // a given SymbolDependency.
            if (!b.getTypedProperties().isEmpty()) {
                var optional_a = a.getProperty(SymbolProperties.OPTIONAL_DEPENDENCIES).orElse(List.of());
                var optional_b = b.getProperty(SymbolProperties.OPTIONAL_DEPENDENCIES).orElse(List.of());

                if (optional_b.isEmpty()) {
                    return a;
                }

                if (optional_a.isEmpty()) {
                    return b;
                }

                var merged = Stream.concat(optional_a.stream(), optional_b.stream())
                        .distinct()
                        .toList();

                return a.toBuilder()
                        .putProperty(SymbolProperties.OPTIONAL_DEPENDENCIES, merged)
                        .build();
            } else {
                return a;
            }
        };
        return symbolStream.sorted()
                .collect(Collectors.groupingBy(SymbolDependency::getDependencyType,
                        Collectors.toMap(SymbolDependency::getPackageName,
                                Function.identity(),
                                guardedMergeWithProperties,
                                TreeMap::new)));
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
                        "Programming Language :: Python :: 3.12",
                        "Programming Language :: Python :: 3.13"
                    ]
                    """, settings.moduleName(), settings.moduleVersion(), settings.moduleDescription());

            Optional.ofNullable(dependencies.get(PythonDependency.Type.DEPENDENCY.getType())).ifPresent(deps -> {
                writer.openBlock("dependencies = [", "]", () -> writeDependencyList(writer, deps.values()));
            });

            Optional<Collection<SymbolDependency>> testDeps =
                    Optional.ofNullable(dependencies.get(PythonDependency.Type.TEST_DEPENDENCY.getType()))
                            .map(Map::values);

            Optional<Collection<SymbolDependency>> docsDeps =
                    Optional.ofNullable(dependencies.get(PythonDependency.Type.DOCS_DEPENDENCY.getType()))
                            .map(Map::values);

            if (testDeps.isPresent() || docsDeps.isPresent()) {
                writer.write("[project.optional-dependencies]");
            }

            testDeps.ifPresent(deps -> {
                writer.openBlock("tests = [", "]", () -> writeDependencyList(writer, deps));
            });

            docsDeps.ifPresent(deps -> {
                writer.openBlock("docs = [", "]", () -> writeDependencyList(writer, deps));
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
                    reportUnusedClass = false

                    [tool.ruff]
                    target-version = "py312"

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
                    dependency.getPackageName(),
                    dependency.getVersion());
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
            return optionals;
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
                writer.write("""
                        ### Documentation

                        $L
                        """, documentation);
            });
            writer.popState();
        });
    }

    /**
     * Write the files required for sphinx doc generation
     */
    private static void writeDocsSkeleton(
            PythonSettings settings,
            GenerationContext context
    ) {
        //TODO Add a configurable flag to disable the generation of the sphinx files
        //TODO Add a configuration that will allow users to select a sphinx theme
        context.writerDelegator().useFileWriter("pyproject.toml", "", writer -> {
            writer.addDependency(SmithyPythonDependency.SPHINX);
            writer.addDependency(SmithyPythonDependency.SPHINX_PYDATA_THEME);
        });
        writeConf(settings, context);
        writeMakeBat(context);
        writeMakeFile(context);
        writeIndexes(context);
    }

    /**
     * Write a conf.py file.
     * A conf.py file is a configuration file used by Sphinx, a documentation
     * generation tool for Python projects. This file contains settings and
     * configurations that control the behavior and appearance of the generated
     * documentation.
     */
    private static void writeConf(
            PythonSettings settings,
            GenerationContext context
    ) {
        var service = context.model().expectShape(settings.service());
        String version = settings.moduleVersion();
        String project = service.getTrait(TitleTrait.class)
                .map(StringTrait::getValue)
                .orElse(service.getTrait(ServiceTrait.class).get().getSdkId());
        context.writerDelegator().useFileWriter("docs/conf.py", "", writer -> {
            writer.write("""
                    import os
                    import sys
                    sys.path.insert(0, os.path.abspath('..'))

                    project = '$L'
                    author = 'Boto'
                    release = '$L'

                    extensions = [
                        'sphinx.ext.autodoc',
                        'sphinx.ext.viewcode',
                    ]

                    templates_path = ['_templates']
                    exclude_patterns = []

                    autodoc_default_options = {
                        'exclude-members': 'deserialize,deserialize_kwargs,serialize,serialize_members'
                    }

                    html_theme = 'pydata_sphinx_theme'
                    html_theme_options = {
                        "logo": {
                            "text": "AWS SDK for Python",
                        }
                    }

                    autodoc_typehints = 'both'
                                """, project, version);
        });
    }

    /**
     * Write a make.bat file.
     * A make.bat file is a batch script used on Windows to build Sphinx documentation.
     * This script sets up the environment and runs the Sphinx build commands.
     *
     * @param context The generation context containing the writer delegator.
     */
    private static void writeMakeBat(
            GenerationContext context
    ) {
        context.writerDelegator().useFileWriter("docs/make.bat", "", writer -> {
            writer.write("""
                    @ECHO OFF

                    pushd %~dp0

                    REM Command file for Sphinx documentation

                    if "%SPHINXBUILD%" == "" (
                        set SPHINXBUILD=sphinx-build
                    )
                    set BUILDDIR=build
                    set SERVICESDIR=source/reference/services
                    set SPHINXOPTS=-j auto
                    set ALLSPHINXOPTS=-d %BUILDDIR%/doctrees %SPHINXOPTS% .

                    if "%1" == "" goto help

                    if "%1" == "clean" (
                        rmdir /S /Q %BUILDDIR%
                        goto end
                    )

                    if "%1" == "html" (
                        %SPHINXBUILD% -b html %ALLSPHINXOPTS% %BUILDDIR%/html
                        echo.
                        echo "Build finished. The HTML pages are in %BUILDDIR%/html."
                        goto end
                    )

                    :help
                    %SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

                    :end
                    popd
                            """);
        });
    }

    /**
     * Write a Makefile.
     * A Makefile is used on Unix-based systems to build Sphinx documentation.
     * This file contains rules for cleaning the build directory and generating HTML documentation.
     *
     * @param context The generation context containing the writer delegator.
     */
    private static void writeMakeFile(
            GenerationContext context
    ) {
        context.writerDelegator().useFileWriter("docs/Makefile", "", writer -> {
            writer.write("""
                    SPHINXBUILD   = sphinx-build
                    BUILDDIR      = build
                    SERVICESDIR   = source/reference/services
                    SPHINXOPTS    = -j auto
                    ALLSPHINXOPTS   = -d $$(BUILDDIR)/doctrees $$(SPHINXOPTS) .

                    clean:
                    \t-rm -rf $$(BUILDDIR)/*

                    html:
                    \t$$(SPHINXBUILD) -b html $$(ALLSPHINXOPTS) $$(BUILDDIR)/html
                    \t@echo
                    \t@echo "Build finished. The HTML pages are in $$(BUILDDIR)/html."
                        """);
        });
    }

    /**
     * Write the main index files for the documentation.
     * This method creates the main index.rst file and additional index files for
     * the client and models sections.
     *
     * @param context The generation context containing the writer delegator.
     */
    private static void writeIndexes(GenerationContext context) {
        // Write the main index file for the documentation
        context.writerDelegator().useFileWriter("docs/index.rst", "", writer -> {
            writer.write("""
                    AWS SDK For Python
                    ====================================================

                    ..  toctree::
                        :maxdepth: 2
                        :titlesonly:
                        :glob:

                        */index
                                """);
        });

        // Write the index file for the client section
        writeIndexFile(context, "docs/client/index.rst", "Client");

        // Write the index file for the models section
        writeIndexFile(context, "docs/models/index.rst", "Models");
    }

    /**
     * Helper method to write an index file with the given title.
     * This method creates an index file at the specified file path with the provided title.
     *
     * @param context  The generation context.
     * @param filePath The file path of the index file.
     * @param title    The title of the index file.
     */
    private static void writeIndexFile(GenerationContext context, String filePath, String title) {
        context.writerDelegator().useFileWriter(filePath, "", writer -> {
            writer.write("""
                    $L
                    =======
                    .. toctree::
                       :maxdepth: 1
                       :titlesonly:
                       :glob:

                       *
                                """, title);
        });
    }

}
