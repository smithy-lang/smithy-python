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

import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Settings used by {@link PythonCodegenPlugin}.
 * TODO: make this immutable
 */
@SmithyUnstableApi
public final class PythonSettings {

    private static final String SERVICE = "service";
    private static final String MODULE_NAME = "module";
    private static final String MODULE_DESCRIPTION = "moduleDescription";
    private static final String MODULE_VERSION = "moduleVersion";

    private ShapeId service;
    private String moduleName;
    private String moduleVersion;
    private String moduleDescription = "";
    private ShapeId protocol;

    /**
     * Create a settings object from a configuration object node.
     *
     * @param config Config object to load.
     * @return Returns the extracted settings.
     */
    public static PythonSettings from(ObjectNode config) {
        PythonSettings settings = new PythonSettings();
        config.warnIfAdditionalProperties(Arrays.asList(SERVICE, MODULE_NAME, MODULE_DESCRIPTION, MODULE_VERSION));

        settings.setService(config.expectStringMember(SERVICE).expectShapeId());
        settings.setModuleName(config.expectStringMember(MODULE_NAME).getValue());
        settings.setModuleVersion(config.expectStringMember(MODULE_VERSION).getValue());
        settings.setModuleDescription(config.getStringMemberOrDefault(
                MODULE_DESCRIPTION, settings.getModuleName() + " client"));

        return settings;
    }

    /**
     * Gets the id of the service that is being generated.
     *
     * @return Returns the service id.
     * @throws NullPointerException if the service has not been set.
     */
    public ShapeId getService() {
        return Objects.requireNonNull(service, SERVICE + " not set");
    }

    /**
     * Gets the corresponding {@link ServiceShape} from a model.
     *
     * @param model Model to search for the service shape by ID.
     * @return Returns the found {@code Service}.
     * @throws NullPointerException if the service has not been set.
     * @throws CodegenException if the service is invalid or not found.
     */
    public ServiceShape getService(Model model) {
        return model
                .getShape(getService())
                .orElseThrow(() -> new CodegenException("Service shape not found: " + getService()))
                .asServiceShape()
                .orElseThrow(() -> new CodegenException("Shape is not a Service: " + getService()));
    }

    /**
     * Sets the service to generate.
     *
     * @param service The service to generate.
     */
    public void setService(ShapeId service) {
        this.service = Objects.requireNonNull(service);
    }

    /**
     * Gets the required module name for the module that will be generated.
     *
     * @return Returns the module name.
     * @throws NullPointerException if the module name has not been set.
     */
    public String getModuleName() {
        return Objects.requireNonNull(moduleName, MODULE_NAME + " not set");
    }

    /**
     * Sets the name of the module to generate.
     *
     * @param moduleName The name of the module to generate.
     */
    public void setModuleName(String moduleName) {
        if (moduleName != null && !moduleName.matches("[a-z_\\d]+")) {
            throw new CodegenException(
                    "Python package names may only consist of lowercase letters, numbers, and underscores.");
        }
        this.moduleName = Objects.requireNonNull(moduleName);
    }

    /**
     * Gets the required module version for the module that will be generated.
     *
     * @return The version of the module that will be generated.
     * @throws NullPointerException if the module version has not been set.
     */
    public String getModuleVersion() {
        return Objects.requireNonNull(moduleVersion, MODULE_VERSION + " not set");
    }

    /**
     * Sets the required module version for the module that will be generated.
     *
     * @param moduleVersion The version of the module that will be generated.
     */
    public void setModuleVersion(String moduleVersion) {
        this.moduleVersion = Objects.requireNonNull(moduleVersion);
    }

    /**
     * Gets the optional module description for the module that will be generated.
     *
     * @return Returns the module description.
     */
    public String getModuleDescription() {
        return moduleDescription;
    }

    /**
     * Sets the description of the module to generate.
     *
     * @param moduleDescription The description of the module to generate.
     */
    public void setModuleDescription(String moduleDescription) {
        this.moduleDescription = Objects.requireNonNull(moduleDescription);
    }

    /**
     * Gets the configured protocol to generate.
     *
     * @return Returns the configured protocol.
     */
    public ShapeId getProtocol() {
        return protocol;
    }

    /**
     * Resolves the highest priority protocol from a service shape that is
     * supported by the generator.
     *
     * @param model Model to enable finding protocols on the service.
     * @param service Service to get the protocols from if "protocols" is not set.
     * @param supportedProtocols The set of protocol names supported by the generator.
     * @return Returns the resolved protocol name.
     * @throws CodegenException if no protocol could be resolved.
     */
    public ShapeId resolveServiceProtocol(Model model, ServiceShape service, Set<ShapeId> supportedProtocols) {
        if (protocol != null) {
            return protocol;
        }

        ServiceIndex serviceIndex = ServiceIndex.of(model);
        Set<ShapeId> resolvedProtocols = serviceIndex.getProtocols(service).keySet();
        if (resolvedProtocols.isEmpty()) {
            throw new CodegenException(
                    "Unable to derive the protocol setting of the service `" + service.getId() + "` because no "
                            + "protocol definition traits were present. You need to set an explicit `protocol` to "
                            + "generate in smithy-build.json to generate this service.");
        }

        protocol = resolvedProtocols.stream()
                .filter(supportedProtocols::contains)
                .findFirst()
                .orElseThrow(() -> new CodegenException(String.format(
                        "The %s service supports the following unsupported protocols %s. The following protocol "
                                + "generators were found on the class path: %s",
                        service.getId(), resolvedProtocols, supportedProtocols)));

        return protocol;
    }

    /**
     * Sets the protocol to generate.
     *
     * @param protocol Protocols to generate.
     */
    public void setProtocol(ShapeId protocol) {
        this.protocol = Objects.requireNonNull(protocol);
    }
}
