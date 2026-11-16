/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import software.amazon.smithy.model.node.ObjectNode;

public class PythonSettingsTest {

    @ParameterizedTest
    @CsvSource({
            "restjson, restjson",
            "test_client, test_client",
            "test-client, test_client",
            "my-test_client, my_test_client"
    })
    public void derivesModuleNameFromConfiguredModule(String module, String expectedModuleName) {
        var settings = fromModule(module);

        assertAll(
                () -> assertEquals(module, settings.packageName()),
                () -> assertEquals(expectedModuleName, settings.moduleName()),
                () -> assertEquals(settings, settings.toBuilder().build()));
    }

    private static PythonSettings fromModule(String module) {
        return PythonSettings.fromNode(ObjectNode.builder()
                .withMember("service", "smithy.example#TestService")
                .withMember("module", module)
                .withMember("moduleVersion", "0.0.1")
                .build());
    }
}
