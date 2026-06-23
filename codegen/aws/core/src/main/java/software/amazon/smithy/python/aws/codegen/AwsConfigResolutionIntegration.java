/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import java.util.Map;
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
        return List.of(
                new PropertyDeclarationInterceptor(context),
                new PropertyInitInterceptor(),
                new PreDeclarationsInterceptor(),
                new PreInitInterceptor(),
                new ConfigTailInterceptor()
        );
    }

    // Replaces plain field declarations with descriptor assignments for properties
    // that have AWS metadata registered.
    private static final class PropertyDeclarationInterceptor
            implements CodeInterceptor<ConfigSection.PropertyDeclarationSection, PythonWriter> {

        private final GenerationContext context;

        PropertyDeclarationInterceptor(GenerationContext context) {
            this.context = context;
        }

        @Override
        public Class<ConfigSection.PropertyDeclarationSection> sectionType() {
            return ConfigSection.PropertyDeclarationSection.class;
        }

        @Override
        public void write(
                PythonWriter writer,
                String previousText,
                ConfigSection.PropertyDeclarationSection section
        ) {
            ConfigProperty prop = section.property();
            AwsConfigPropertyMetadata meta = DESCRIPTOR_METADATA.get(prop.name());

            if (meta == null) {
                writer.write(previousText.stripTrailing());
                return;
            }

            String typeHint = prop.type().getName();
            if (prop.isNullable() && !typeHint.endsWith("| None")) {
                typeHint = typeHint + " | None";
            }
            writer.write("$L: $L = _descriptors['$L']  # type: ignore[assignment]",
                    prop.name(), typeHint, prop.name());
            writer.writeDocs(prop.documentation(), context);
        }
    }

    // Skips `self.X = X` initialization for descriptor properties since the
    // descriptor handles resolution.
    private static final class PropertyInitInterceptor
            implements CodeInterceptor<ConfigProperty.InitializeConfigPropertySection, PythonWriter> {

        @Override
        public Class<ConfigProperty.InitializeConfigPropertySection> sectionType() {
            return ConfigProperty.InitializeConfigPropertySection.class;
        }

        @Override
        public void write(
                PythonWriter writer,
                String previousText,
                ConfigProperty.InitializeConfigPropertySection section
        ) {
            if (DESCRIPTOR_METADATA.containsKey(section.property().name())) {
                return;
            }
            writer.write(previousText.stripTrailing());
        }
    }

    // Injects _descriptors dict and _resolver field before property declarations.
    private static final class PreDeclarationsInterceptor
            implements CodeInterceptor<ConfigSection.PrePropertyDeclarationsSection, PythonWriter> {

        @Override
        public Class<ConfigSection.PrePropertyDeclarationsSection> sectionType() {
            return ConfigSection.PrePropertyDeclarationsSection.class;
        }

        @Override
        public void write(
                PythonWriter writer,
                String previousText,
                ConfigSection.PrePropertyDeclarationsSection section
        ) {
            List<ConfigProperty> descriptorProps = section.properties().stream()
                    .filter(p -> DESCRIPTOR_METADATA.containsKey(p.name()))
                    .collect(Collectors.toList());

            if (descriptorProps.isEmpty()) {
                return;
            }

            addImports(writer, descriptorProps);

            writer.write("# Config properties using descriptors");
            writer.openBlock("_descriptors = {");
            for (ConfigProperty prop : descriptorProps) {
                AwsConfigPropertyMetadata meta = DESCRIPTOR_METADATA.get(prop.name());
                StringBuilder sb = new StringBuilder();
                sb.append("'").append(prop.name()).append("': ConfigProperty('")
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
                writer.write(sb.toString());
            }
            writer.closeBlock("}");
            writer.write("");
            writer.write("_resolver: ConfigResolver");
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
    }

    // Injects resolver initialization at the start of __init__.
    private static final class PreInitInterceptor
            implements CodeInterceptor<ConfigSection.PreInitializePropertiesSection, PythonWriter> {

        @Override
        public Class<ConfigSection.PreInitializePropertiesSection> sectionType() {
            return ConfigSection.PreInitializePropertiesSection.class;
        }

        @Override
        public void write(
                PythonWriter writer,
                String previousText,
                ConfigSection.PreInitializePropertiesSection section
        ) {
            boolean hasDescriptors = section.properties().stream()
                    .anyMatch(p -> DESCRIPTOR_METADATA.containsKey(p.name()));

            if (!hasDescriptors) {
                return;
            }

            writer.write("self._resolver = ConfigResolver(sources=[EnvironmentSource()])");
            writer.write("");
            writer.write("# Only set if provided (not None) to allow resolution from sources");
            writer.write("for key in self.__class__._descriptors.keys():");
            writer.indent();
            writer.write("value = locals().get(key)");
            writer.write("if value is not None:");
            writer.indent();
            writer.write("setattr(self, key, value)");
            writer.dedent();
            writer.dedent();
        }
    }

    // Appends get_source() method to the Config class.
    private static final class ConfigTailInterceptor
            implements CodeInterceptor<ConfigSection, PythonWriter> {

        @Override
        public Class<ConfigSection> sectionType() {
            return ConfigSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, ConfigSection section) {
            boolean hasDescriptors = section.properties().stream()
                    .anyMatch(p -> DESCRIPTOR_METADATA.containsKey(p.name()));

            writer.write(previousText.stripTrailing());

            if (!hasDescriptors) {
                return;
            }

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
    }
}
