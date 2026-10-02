/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

public class OperationInputGeneratorTest {

    @ParameterizedTest
    @CsvSource({
            // Ordinary members are untouched.
            "city_id, city_id",
            "config, config",
            "call, call",
            "input, input",
            "pipeline, pipeline",
            "deepcopy, deepcopy",
            "user_agent_plugin, user_agent_plugin",
            // Reserved names are escaped, and the escape is closed over trailing
            // underscores so it never steals a keyword another member already owns.
            "self, self_",
            "self_, self__",
            "plugins, plugins_",
            "plugins_, plugins__",
            "plugins___, plugins____",
            // Generated locals are underscore-prefixed, so members that are too.
            "_input, _input_",
            "_config, _config_"
    })
    public void escapesOnlyNamesThatCouldShadowGeneratedOnes(String memberName, String expected) {
        assertEquals(expected, OperationInputGenerator.parameterName(memberName));
    }

    @Test
    public void escapeIsInjective() {
        var names = List.of("self",
                "self_",
                "self__",
                "plugins",
                "plugins_",
                "plugins__",
                "_plugins",
                "_plugins_",
                "_input",
                "_input_",
                "input",
                "config",
                "plugin");
        var parameters = new HashSet<String>();
        for (var name : names) {
            var parameter = OperationInputGenerator.parameterName(name);
            assertTrue(parameters.add(parameter), "Two members map to `" + parameter + "`");
        }
    }
}
