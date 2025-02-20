/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.Arrays;
import java.util.Objects;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.StringUtils;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Settings used by {@link PythonClientCodegenPlugin}.
 *
 * @param service The id of the service that is being generated.
 * @param moduleName The name of the module to generate.
 * @param moduleVersion The version of the module to generate.
 * @param moduleDescription The optional module description for the module that will be generated.
 */
@SmithyUnstableApi
public record PythonSettings(
        ShapeId service,
        String moduleName,
        String moduleVersion,
        String moduleDescription) implements ToSmithyBuilder<PythonSettings> {

    private static final String SERVICE = "service";
    private static final String MODULE_NAME = "module";
    private static final String MODULE_DESCRIPTION = "moduleDescription";
    private static final String MODULE_VERSION = "moduleVersion";

    public PythonSettings {
        Objects.requireNonNull(service);
        Objects.requireNonNull(moduleName);
        Objects.requireNonNull(moduleDescription);
        Objects.requireNonNull(moduleVersion);
        if (!moduleName.matches("[a-z_\\d]+")) {
            throw new CodegenException(
                    "Python package names may only consist of lowercase letters, numbers, and underscores.");
        }
    }

    public PythonSettings(Builder builder) {
        this(
                builder.service,
                builder.moduleName,
                builder.moduleVersion,
                StringUtils.isBlank(builder.moduleDescription)
                        ? builder.moduleName + " client"
                        : builder.moduleDescription);
    }

    /**
     * Gets the corresponding {@link ServiceShape} from a model.
     *
     * @param model Model to search for the service shape by ID.
     * @return Returns the found {@code Service}.
     * @throws NullPointerException if the service has not been set.
     * @throws CodegenException if the service is invalid or not found.
     */
    public ServiceShape service(Model model) {
        return model
                .getShape(service())
                .orElseThrow(() -> new CodegenException("Service shape not found: " + service()))
                .asServiceShape()
                .orElseThrow(() -> new CodegenException("Shape is not a Service: " + service()));
    }

    /**
     * Create a settings object from a configuration object node.
     *
     * @param config Config object to load.
     * @return Returns the extracted settings.
     */
    public static PythonSettings fromNode(ObjectNode config) {
        config.warnIfAdditionalProperties(Arrays.asList(SERVICE, MODULE_NAME, MODULE_DESCRIPTION, MODULE_VERSION));

        String moduleName = config.expectStringMember(MODULE_NAME).getValue();
        Builder builder = builder()
                .service(config.expectStringMember(SERVICE).expectShapeId())
                .moduleName(moduleName)
                .moduleVersion(config.expectStringMember(MODULE_VERSION).getValue());
        config.getStringMember(MODULE_DESCRIPTION).map(StringNode::getValue).ifPresent(builder::moduleDescription);
        return builder.build();
    }

    @Override
    public SmithyBuilder<PythonSettings> toBuilder() {
        return builder()
                .service(service)
                .moduleName(moduleName)
                .moduleVersion(moduleVersion)
                .moduleDescription(moduleDescription);
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder implements SmithyBuilder<PythonSettings> {

        private ShapeId service;
        private String moduleName;
        private String moduleVersion;
        private String moduleDescription;

        @Override
        public PythonSettings build() {
            SmithyBuilder.requiredState("service", service);
            SmithyBuilder.requiredState("moduleName", moduleName);
            SmithyBuilder.requiredState("moduleVersion", moduleVersion);
            return new PythonSettings(this);
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
    }
}
