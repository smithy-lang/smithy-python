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
        setupDocs(settings, context);
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
                        "Programming Language :: Python :: 3.13",
                        "Programming Language :: Python :: 3.14"
                    ]
                    """, settings.moduleName(), settings.moduleVersion(), settings.moduleDescription());

            Optional.ofNullable(dependencies.get(PythonDependency.Type.DEPENDENCY.getType())).ifPresent(deps -> {
                writer.openBlock("dependencies = [", "]\n", () -> writeDependencyList(writer, deps.values()));
            });

            Optional<Collection<SymbolDependency>> testDeps =
                    Optional.ofNullable(dependencies.get(PythonDependency.Type.TEST_DEPENDENCY.getType()))
                            .map(Map::values);

            Optional<Collection<SymbolDependency>> docsDeps =
                    Optional.ofNullable(dependencies.get(PythonDependency.Type.DOCS_DEPENDENCY.getType()))
                            .map(Map::values);

            if (testDeps.isPresent() || docsDeps.isPresent()) {
                writer.write("[dependency-groups]");
            }

            testDeps.ifPresent(deps -> {
                writer.openBlock("test = [", "]\n", () -> writeDependencyList(writer, deps));
            });

            docsDeps.ifPresent(deps -> {
                writer.openBlock("docs = [", "]\n", () -> writeDependencyList(writer, deps));
            });

            // TODO: remove the pyright global suppressions after the serde redo is done
            writer.write("""
                    [build-system]
                    requires = ["hatchling"]
                    build-backend = "hatchling.build"

                    [tool.hatch.build.targets.bdist]
                    exclude = [
                      "tests",
                      "docs",
                    ]

                    [tool.pyright]
                    typeCheckingMode = "strict"
                    reportPrivateUsage = false
                    reportUnusedFunction = false
                    reportUnusedVariable = false
                    reportUnnecessaryComparison = false
                    reportUnusedClass = false
                    enableExperimentalFeatures = true

                    [tool.ruff]
                    target-version = "py312"

                    [tool.ruff.lint]
                    ignore = ["F841"]

                    [tool.ruff.format]
                    skip-magic-trailing-comma = true

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
                        """, writer.formatDocs(documentation, context));
            });
            writer.popState();
        });
    }

    /**
     * Setup files and dependencies for MkDocs documentation generation.
     *
     * MkDocs documentation is only generated for AWS services. Generic clients
     * receive docstrings but are free to choose their own documentation approach.
     */
    private static void setupDocs(
            PythonSettings settings,
            GenerationContext context
    ) {
        // Skip generic services
        if (!CodegenUtils.isAwsService(context)) {
            return;
        }

        context.writerDelegator().useFileWriter("pyproject.toml", "", writer -> {
            writer.addDependency(SmithyPythonDependency.MKDOCS);
            writer.addDependency(SmithyPythonDependency.MKDOCSTRINGS);
            writer.addDependency(SmithyPythonDependency.MKDOCS_MATERIAL);
        });

        var service = context.model().expectShape(settings.service());
        String projectName = service.getTrait(ServiceTrait.class)
                .map(ServiceTrait::getSdkId)
                .orElseGet(() -> service.getTrait(TitleTrait.class)
                        .map(StringTrait::getValue)
                        .orElse(context.settings().service().getName()));
        writeMkDocsConfig(context, projectName);
        writeDocsReadme(context);
    }

    /**
     * Write mkdocs.yml configuration file.
     * This file configures MkDocs, a static site generator for project documentation.
     */
    private static void writeMkDocsConfig(
            GenerationContext context,
            String projectName
    ) {
        context.writerDelegator().useFileWriter("mkdocs.yml", "", writer -> {
            writer.write("""
                    site_name: AWS $1L
                    site_description: Documentation for $1L Client

                    copyright: Copyright &copy; 2025, Amazon Web Services, Inc
                    repo_name: awslabs/aws-sdk-python
                    repo_url: https://github.com/awslabs/aws-sdk-python

                    theme:
                      name: material
                      palette:
                        - scheme: default
                          primary: white
                          accent: light blue
                          toggle:
                            icon: material/brightness-7
                            name: Switch to dark mode
                        - scheme: slate
                          primary: black
                          accent: light blue
                          toggle:
                            icon: material/brightness-4
                            name: Switch to light mode
                      features:
                        - navigation.top
                        - search.suggest
                        - search.highlight
                        - content.code.copy

                    plugins:
                      - search
                      - mkdocstrings:
                          handlers:
                            python:
                              options:
                                show_source: true
                                show_signature: true
                                show_signature_annotations: true
                                show_root_heading: true
                                show_root_full_path: false
                                show_object_full_path: false
                                show_symbol_type_heading: true
                                show_symbol_type_toc: true
                                show_category_heading: true
                                group_by_category: true
                                separate_signature: true
                                signature_crossrefs: true
                                filters:
                                - "!^_"
                                - "!^deserialize"
                                - "!^serialize"

                    markdown_extensions:
                      - pymdownx.highlight
                      - pymdownx.inlinehilite
                      - pymdownx.snippets
                      - pymdownx.superfences
                      - admonition
                      - def_list
                      - toc:
                          permalink: true
                          toc_depth: 3

                    nav:
                      - $1L: index.md

                    extra:
                        social:
                        - icon: fontawesome/brands/github
                          link: https://github.com/awslabs/aws-sdk-python
                    extra_css:
                        - stylesheets/extra.css
                    """, projectName);
        });
    }

    /**
     * Write the readme in the docs folder describing instructions for generation
     *
     * @param context The generation context containing the writer delegator.
     */
    private static void writeDocsReadme(
            GenerationContext context
    ) {
        context.writerDelegator().useFileWriter("docs/README.md", writer -> {
            writer.write("""
                    ## Generating Documentation

                    Material for MkDocs is used for documentation. You can generate HTML locally with the
                    following:

                    ```bash
                    # Install documentation dependencies
                    uv pip install --group docs

                    # Serve documentation locally
                    mkdocs serve

                    # OR build static HTML documentation
                    mkdocs build
                    ```
                    """);
        });
    }

}
