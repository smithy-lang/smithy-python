/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;

/**
 * Integration that generates LICENSE and NOTICE files for AWS Python clients.
 */
public class AwsLicenseAndNoticeIntegration implements PythonIntegration {

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return List.of(
                RuntimeClientPlugin.builder()
                        .writeAdditionalFiles((c) -> {
                            writeLicense(c);
                            writeNotice(c);
                            return List.of();
                        })
                        .build());
    }

    private static void writeLicense(GenerationContext context) {
        context.writerDelegator().useFileWriter("LICENSE", writer -> {
            writer.write(loadResourceAsString("/software/amazon/smithy/python/codegen/apache-2.0-license.txt"));
        });
    }

    private static void writeNotice(GenerationContext context) {
        context.writerDelegator().useFileWriter("NOTICE", writer -> {
            writer.write("Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.");
        });
    }

    private static String loadResourceAsString(String resourcePath) {
        try (InputStream inputStream = AwsLicenseAndNoticeIntegration.class.getResourceAsStream(resourcePath);
                BufferedReader reader =
                        new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
            return reader.lines().collect(Collectors.joining("\n"));
        } catch (Exception e) {
            throw new RuntimeException("Failed to load resource: " + resourcePath, e);
        }
    }
}
