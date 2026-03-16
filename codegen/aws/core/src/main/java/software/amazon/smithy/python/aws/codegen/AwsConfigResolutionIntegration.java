/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.ConfigSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Intercepts the generated Config class to add AWS-specific descriptor-based
 * config resolution, keeping the generic ConfigGenerator unchanged.
 */
@SmithyInternalApi
public class AwsConfigResolutionIntegration implements PythonIntegration {

    // Metadata for properties that use descriptors, keyed by property name.
    private static final Map<String, AwsConfigPropertyMetadata> DESCRIPTOR_METADATA = Map.of(
            "region", AwsConfiguration.REGION_METADATA,
            "retry_strategy", AwsConfiguration.RETRY_STRATEGY_METADATA,
            "sdk_ua_app_id", AwsUserAgentIntegration.SDK_UA_APP_ID_METADATA
    );

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        return List.of(new ConfigResolutionInterceptor());
    }

    private static final class ConfigResolutionInterceptor
            implements CodeInterceptor<ConfigSection, PythonWriter> {

        @Override
        public Class<ConfigSection> sectionType() {
            return ConfigSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, ConfigSection section) {
            // Find properties that have descriptor metadata registered
            List<ConfigProperty> descriptorProps = section.properties().stream()
                    .filter(p -> DESCRIPTOR_METADATA.containsKey(p.name()))
                    .collect(Collectors.toList());

            if (descriptorProps.isEmpty()) {
                writer.write(previousText);
                return;
            }

            Set<String> descriptorNames = descriptorProps.stream()
                    .map(ConfigProperty::name)
                    .collect(Collectors.toSet());

            addImports(writer, descriptorProps);

            String transformed = transformConfigClass(previousText, descriptorProps, descriptorNames);
            writer.write(transformed);

            appendGetSourceMethod(writer);
        }

        private void addImports(PythonWriter writer, List<ConfigProperty> descriptorProps) {
            writer.addImport("smithy_aws_core.config.property", "ConfigProperty");
            writer.addImport("smithy_aws_core.config.resolver", "ConfigResolver");
            writer.addImport("smithy_aws_core.config.sources", "EnvironmentSource");
            writer.addImport("smithy_aws_core.config.source_info", "SourceInfo");

            for (ConfigProperty prop : descriptorProps) {
                AwsConfigPropertyMetadata meta = DESCRIPTOR_METADATA.get(prop.name());
                if (meta == null) {
                    continue;
                }
                meta.validatorOpt().ifPresent(sym ->
                        writer.addImport(sym.getNamespace(), sym.getName()));
                meta.customResolverOpt().ifPresent(sym ->
                        writer.addImport(sym.getNamespace(), sym.getName()));
                meta.defaultValueOpt().ifPresent(val -> {
                    if (val.contains("RetryStrategyOptions")) {
                        writer.addImport("smithy_core.retries", "RetryStrategyOptions");
                    }
                });
            }
        }

        private void appendGetSourceMethod(PythonWriter writer) {
            writer.write("""

                    def get_source(self, key: str) -> SourceInfo | None:
                        \"""Get the source that provided a configuration value.

                        Args:
                            key: The configuration key (e.g., 'region', 'retry_strategy')

                        Returns:
                            The source info (SimpleSource or ComplexSource),
                            or None if the key hasn't been resolved yet.
                        \"""
                        cached = self.__dict__.get(f'_cache_{key}')
                        return cached[1] if cached else None
                """);
        }

        private String transformConfigClass(
                String previousText,
                List<ConfigProperty> descriptorProps,
                Set<String> descriptorNames
        ) {
            String[] lines = previousText.split("\n", -1);
            List<String> result = new ArrayList<>();

            boolean inClassBody = false;
            boolean inInit = false;
            boolean initParamsStarted = false;
            boolean initBodyStarted = false;
            boolean descriptorsInserted = false;
            boolean resolverInitInserted = false;
            int i = 0;

            while (i < lines.length) {
                String line = lines[i];
                String trimmed = line.trim();

                if (trimmed.startsWith("class Config")) {
                    inClassBody = true;
                    result.add(line);
                    i++;
                    continue;
                }

                // Skip field declarations for descriptor properties
                if (inClassBody && !inInit) {
                    boolean isDescriptorField = false;
                    for (String name : descriptorNames) {
                        if (trimmed.startsWith(name + ":") || trimmed.startsWith(name + " :")) {
                            isDescriptorField = true;
                            break;
                        }
                    }
                    if (isDescriptorField) {
                        i++;
                        // Skip following docstring if present
                        while (i < lines.length) {
                            String nextTrimmed = lines[i].trim();
                            if (nextTrimmed.startsWith("\"\"\"")) {
                                if (nextTrimmed.endsWith("\"\"\"") && nextTrimmed.length() > 3) {
                                    i++;
                                } else {
                                    i++;
                                    while (i < lines.length && !lines[i].trim().endsWith("\"\"\"")) {
                                        i++;
                                    }
                                    i++;
                                }
                                break;
                            } else if (nextTrimmed.isEmpty()) {
                                i++;
                            } else {
                                break;
                            }
                        }
                        continue;
                    }
                }

                // Detect __init__ definition start
                if (trimmed.startsWith("def __init__(")) {
                    inInit = true;
                    initParamsStarted = true;

                    if (!descriptorsInserted) {
                        insertDescriptorDeclarations(result, descriptorProps);
                        descriptorsInserted = true;
                    }

                    result.add(line);
                    i++;
                    continue;
                }

                // Detect end of __init__ params
                if (initParamsStarted && !initBodyStarted && trimmed.equals("):")) {
                    result.add(line);
                    initBodyStarted = true;
                    i++;
                    continue;
                }

                // Insert resolver initialization at start of __init__ body
                if (initBodyStarted && !resolverInitInserted) {
                    if (!trimmed.isEmpty()) {
                        insertResolverInitialization(result, descriptorNames);
                        resolverInitInserted = true;
                    }
                }

                // Skip self.X = X for descriptor properties in __init__ body
                if (initBodyStarted) {
                    boolean isDescriptorInit = false;
                    for (String name : descriptorNames) {
                        if (trimmed.equals("self." + name + " = " + name)) {
                            isDescriptorInit = true;
                            break;
                        }
                    }
                    if (isDescriptorInit) {
                        i++;
                        continue;
                    }
                }

                result.add(line);
                i++;
            }

            return String.join("\n", result);
        }

        private void insertDescriptorDeclarations(List<String> result, List<ConfigProperty> descriptorProps) {
            result.add("    # Config properties using descriptors");
            result.add("    _descriptors = {");
            for (ConfigProperty prop : descriptorProps) {
                AwsConfigPropertyMetadata meta = DESCRIPTOR_METADATA.get(prop.name());
                StringBuilder sb = new StringBuilder();
                sb.append("        '").append(prop.name()).append("': ConfigProperty('")
                        .append(prop.name()).append("'");
                if (meta != null) {
                    meta.validatorOpt().ifPresent(sym ->
                            sb.append(", validator=").append(sym.getName()));
                    meta.customResolverOpt().ifPresent(sym ->
                            sb.append(", resolver_func=").append(sym.getName()));
                    meta.defaultValueOpt().ifPresent(val ->
                            sb.append(", default_value=").append(val));
                }
                sb.append("),");
                result.add(sb.toString());
            }
            result.add("    }");
            result.add("");

            // Add class-level descriptor assignments with type hints
            for (ConfigProperty prop : descriptorProps) {
                String typeHint = prop.type().getName();
                if (prop.isNullable() && !typeHint.endsWith("| None")) {
                    typeHint = typeHint + " | None";
                }
                result.add("    " + prop.name() + ": " + typeHint +
                        " = _descriptors['" + prop.name() + "']  # type: ignore[assignment]");

                if (!prop.documentation().isEmpty()) {
                    String doc = prop.documentation();
                    if (doc.contains("\n")) {
                        result.add("    \"\"\"");
                        for (String docLine : doc.split("\n")) {
                            result.add("    " + docLine);
                        }
                        result.add("    \"\"\"");
                    } else {
                        result.add("    \"\"\"" + doc + "\"\"\"");
                    }
                }
                result.add("");
            }

            // Add _resolver field declaration
            result.add("    _resolver: ConfigResolver");
            result.add("");
        }

        private void insertResolverInitialization(List<String> result, Set<String> descriptorNames) {
            result.add("        # Set instance values for descriptor properties");
            result.add("        self._resolver = ConfigResolver(sources=[EnvironmentSource()])");
            result.add("");
            result.add("        # Only set if provided (not None) to allow resolution from sources");
            result.add("        for key in self.__class__._descriptors.keys():");
            result.add("            value = locals().get(key)");
            result.add("            if value is not None:");
            result.add("                setattr(self, key, value)");
            result.add("");
        }
    }
}
