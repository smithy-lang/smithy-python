/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.protocols.AwsQueryTrait;
import software.amazon.smithy.aws.traits.protocols.Ec2QueryTrait;
import software.amazon.smithy.aws.traits.protocols.RestXmlTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds configurable XML deserialization to clients that support an XML protocol.
 */
@SmithyInternalApi
public final class XmlDeserializationIntegration implements PythonIntegration {
    private static final Set<ShapeId> XML_PROTOCOLS = Set.of(
            RestXmlTrait.ID,
            AwsQueryTrait.ID,
            Ec2QueryTrait.ID);

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var protocolGenerator = context.protocolGenerator();
        if (protocolGenerator == null || !isXmlProtocol(protocolGenerator.getProtocol())) {
            return List.of();
        }

        var mode = Symbol.builder()
                .name("XMLDeserializationMode")
                .namespace("smithy_xml", ".")
                .addDependency(SmithyPythonDependency.SMITHY_XML)
                .build();
        var plugin = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .name("xml_deserialization_plugin")
                        .namespace("smithy_xml.plugins", ".")
                        .addDependency(SmithyPythonDependency.SMITHY_XML)
                        .build())
                .build();
        var property = ConfigProperty.builder()
                .name("xml_deserialization_mode")
                .type(mode)
                .documentation(
                        "Controls whether XML response payloads are deserialized eagerly or incrementally.")
                .nullable(true)
                .build();

        return List.of(RuntimeClientPlugin.builder()
                .addConfigProperty(property)
                .pythonPlugin(plugin)
                .build());
    }

    static boolean isXmlProtocol(ShapeId protocol) {
        return XML_PROTOCOLS.contains(protocol);
    }
}
