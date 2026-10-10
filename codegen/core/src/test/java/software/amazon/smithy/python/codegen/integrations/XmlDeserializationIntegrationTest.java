/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.aws.traits.protocols.AwsQueryTrait;
import software.amazon.smithy.aws.traits.protocols.Ec2QueryTrait;
import software.amazon.smithy.aws.traits.protocols.RestXmlTrait;
import software.amazon.smithy.model.shapes.ShapeId;

public class XmlDeserializationIntegrationTest {
    @Test
    public void detectsXmlProtocols() {
        assertTrue(XmlDeserializationIntegration.isXmlProtocol(RestXmlTrait.ID));
        assertTrue(XmlDeserializationIntegration.isXmlProtocol(AwsQueryTrait.ID));
        assertTrue(XmlDeserializationIntegration.isXmlProtocol(Ec2QueryTrait.ID));
        assertFalse(XmlDeserializationIntegration.isXmlProtocol(ShapeId.from("example#other")));
    }
}
