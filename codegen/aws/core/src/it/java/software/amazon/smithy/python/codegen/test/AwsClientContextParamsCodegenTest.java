/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.build.PluginContext;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.python.codegen.PythonClientCodegenPlugin;

public class AwsClientContextParamsCodegenTest {

    private static String generateConfig(Path tempDir, String resource, String service, String module)
            throws IOException {
        var loader = AwsClientContextParamsCodegenTest.class.getClassLoader();
        Model model = Model.assembler(loader)
                .discoverModels(loader)
                .addImport(AwsClientContextParamsCodegenTest.class.getResource(resource))
                .assemble()
                .unwrap();
        PluginContext context = PluginContext.builder()
                .fileManifest(FileManifest.create(tempDir))
                .settings(ObjectNode.builder()
                        .withMember("service", service)
                        .withMember("module", module)
                        .withMember("moduleVersion", "0.0.1")
                        .build())
                .model(model)
                .build();
        new PythonClientCodegenPlugin().execute(context);
        return Files.readString(tempDir.resolve("src/" + module + "/config.py"));
    }

    @Test
    public void addsAsyncConfigFieldsForClientContextParams(@TempDir Path tempDir) throws IOException {
        var config = generateConfig(
                tempDir,
                "aws-client-context-params.smithy",
                "example.awsccp#ClientContextService",
                "awsccp");
        // Overrides, dataclass fields and FieldSpecs without resolvers.
        assertTrue(config.contains("    force_path_style: bool | None\n"));
        assertTrue(config.contains("force_path_style: bool | None = None"));
        assertTrue(config.contains("Forces path-style addressing."));
        assertTrue(config.contains("stage: str | None = None"));
        assertTrue(config.contains("\"force_path_style\": FieldSpec(default=None),"));
        assertTrue(config.contains("\"disable_s3_express_session_auth\": FieldSpec(default=None),"));
        assertTrue(config.contains("\"stage\": FieldSpec(default=None),"));
        // ForcePathStyle is both a built-in and a client context parameter: one field.
        assertEquals(1, count(config, "force_path_style: bool | None = None"));
        assertEquals(1, count(config, "\"force_path_style\": FieldSpec("));
        // This service's rules declare none of the AWS built-ins with generated fields.
        assertFalse(config.contains("use_fips_endpoint"));
        assertFalse(config.contains("use_dualstack_endpoint"));
        assertFalse(config.contains("account_id_endpoint_mode"));
    }

    @Test
    public void addsAccountIdEndpointModeWhenRulesDeclareIt(@TempDir Path tempDir) throws IOException {
        var config = generateConfig(
                tempDir,
                "aws-account-id-endpoint-mode.smithy",
                "example.accountid#AccountIdService",
                "accountid");
        assertTrue(config.contains("    account_id_endpoint_mode: str | None\n"));
        assertEquals(1, count(config, "account_id_endpoint_mode: str | None = None"));
        assertTrue(config.contains("Defaults to preferred."));
        assertTrue(config.contains("\"account_id_endpoint_mode\": FieldSpec(default=\"preferred\"),"));
        // Its rules declare no FIPS or dual-stack built-ins.
        assertFalse(config.contains("use_fips_endpoint"));
        assertFalse(config.contains("use_dualstack_endpoint"));
    }

    private static int count(String text, String fragment) {
        int count = 0;
        for (int i = text.indexOf(fragment); i >= 0; i = text.indexOf(fragment, i + 1)) {
            count++;
        }
        return count;
    }
}
