/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.types;

import java.util.Arrays;
import java.util.Optional;
import software.amazon.smithy.model.node.BooleanNode;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.selector.Selector;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Settings used by {@link PythonTypeCodegenPlugin}.
 *
 * @param service The id of the service that is being generated.
 * @param moduleName The name of the module to generate.
 * @param moduleVersion The version of the module to generate.
 * @param moduleDescription The optional module description for the module that will be generated.
 * @param selector An optional selector to reduce the set of shapes to be generated.
 */
@SmithyUnstableApi
public record PythonTypeCodegenSettings(
        Optional<ShapeId> service,
        String moduleName,
        String moduleVersion,
        String moduleDescription,
        Selector selector,
        Boolean generateInputsAndOutputs) implements ToSmithyBuilder<PythonTypeCodegenSettings> {

    private static final String SERVICE = "service";
    private static final String MODULE_NAME = "module";
    private static final String MODULE_DESCRIPTION = "moduleDescription";
    private static final String MODULE_VERSION = "moduleVersion";
    private static final String SELECTOR = "selector";
    private static final String GENERATE_INPUTS_AND_OUTPUTS = "generateInputsAndOutputs";

    private PythonTypeCodegenSettings(Builder builder) {
        this(
                Optional.ofNullable(builder.service),
                builder.moduleName,
                builder.moduleVersion,
                builder.moduleDescription,
                builder.selector,
                builder.generateInputsAndOutputs);
    }

    @Override
    public Builder toBuilder() {
        Builder builder = builder()
                .moduleName(moduleName)
                .moduleVersion(moduleVersion)
                .moduleDescription(moduleDescription)
                .selector(selector)
                .generateInputsAndOutputs(generateInputsAndOutputs);
        service.ifPresent(builder::service);
        return builder;
    }

    public PythonSettings toPythonSettings(ShapeId service) {
        return PythonSettings.builder()
                .service(service)
                .moduleName(moduleName)
                .moduleVersion(moduleVersion)
                .moduleDescription(moduleDescription)
                .artifactType(PythonSettings.ArtifactType.TYPES)
                .build();
    }

    public PythonSettings toPythonSettings() {
        return toPythonSettings(service.get());
    }

    /**
     * Create a settings object from a configuration object node.
     *
     * @param config Config object to load.
     * @return Returns the extracted settings.
     */
    public static PythonTypeCodegenSettings fromNode(ObjectNode config) {
        config.warnIfAdditionalProperties(Arrays.asList(SERVICE, MODULE_NAME, MODULE_DESCRIPTION, MODULE_VERSION));

        String moduleName = config.expectStringMember(MODULE_NAME).getValue();
        Builder builder = builder()
                .moduleName(moduleName)
                .moduleVersion(config.expectStringMember(MODULE_VERSION).getValue());
        config.getStringMember(SERVICE).map(StringNode::expectShapeId).ifPresent(builder::service);
        config.getStringMember(MODULE_DESCRIPTION).map(StringNode::getValue).ifPresent(builder::moduleDescription);
        config.getStringMember(SELECTOR).map(node -> Selector.parse(node.getValue())).ifPresent(builder::selector);
        config.getBooleanMember(GENERATE_INPUTS_AND_OUTPUTS)
                .map(BooleanNode::getValue)
                .ifPresent(builder::generateInputsAndOutputs);
        return builder.build();
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder implements SmithyBuilder<PythonTypeCodegenSettings> {

        private ShapeId service;
        private String moduleName;
        private String moduleVersion;
        private String moduleDescription;
        private Selector selector = Selector.IDENTITY;
        private Boolean generateInputsAndOutputs = false;

        @Override
        public PythonTypeCodegenSettings build() {
            SmithyBuilder.requiredState("moduleName", moduleName);
            SmithyBuilder.requiredState("moduleVersion", moduleVersion);
            return new PythonTypeCodegenSettings(this);
        }

        public Builder service(ShapeId service) {
            this.service = service;
            return this;
        }

        public Builder moduleName(String moduleName) {
            this.moduleName = moduleName;
            return this;
        }

        public Builder moduleVersion(String moduleVersion) {
            this.moduleVersion = moduleVersion;
            return this;
        }

        public Builder moduleDescription(String moduleDescription) {
            this.moduleDescription = moduleDescription;
            return this;
        }

        public Builder selector(Selector selector) {
            this.selector = selector == null ? Selector.IDENTITY : selector;
            return this;
        }

        public Builder generateInputsAndOutputs(boolean generateInputsAndOutputs) {
            this.generateInputsAndOutputs = generateInputsAndOutputs;
            return this;
        }
    }
}
