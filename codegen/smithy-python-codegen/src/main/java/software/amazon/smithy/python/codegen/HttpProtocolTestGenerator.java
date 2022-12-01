/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import java.util.TreeSet;
import java.util.logging.Logger;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.protocoltests.traits.AppliesTo;
import software.amazon.smithy.protocoltests.traits.HttpMessageTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestCase;
import software.amazon.smithy.protocoltests.traits.HttpRequestTestsTrait;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestCase;
import software.amazon.smithy.protocoltests.traits.HttpResponseTestsTrait;
import software.amazon.smithy.utils.CaseUtils;

/**
 * Generates protocol tests for a given HTTP protocol.
 *
 * <p>This should preferably be instantiated and used within an
 * implementation of a `ProtocolGeneration`
 */
public final class HttpProtocolTestGenerator implements Runnable {

    private static final Logger LOGGER = Logger.getLogger(HttpProtocolTestGenerator.class.getName());

    private final PythonSettings settings;
    private final Model model;
    private final ShapeId protocol;
    private final ServiceShape service;
    private final PythonWriter writer;
    private final GenerationContext context;

    public HttpProtocolTestGenerator(
            GenerationContext context,
            ShapeId protocol,
            PythonWriter writer
    ) {
        this.settings = context.settings();
        this.model = context.model();
        this.protocol = protocol;
        this.service = settings.getService(model);
        this.writer = writer;
        this.context = context;
    }

    /**
     * Generates the HTTP-based protocol tests for the given protocol in the model.
     */
    @Override
    public void run() {
        OperationIndex operationIndex = OperationIndex.of(model);
        TopDownIndex topDownIndex = TopDownIndex.of(model);

        // Use a TreeSet to have a fixed ordering of tests.
        for (OperationShape operation : new TreeSet<>(topDownIndex.getContainedOperations(service))) {

            // TODO: Add settings to configure which tests are generated (client or server)
            generateOperationTests(AppliesTo.CLIENT, operation, operationIndex);
        }
    }

    private void generateOperationTests(
            AppliesTo implementation,
            OperationShape operation,
            OperationIndex operationIndex) {

        // Request Tests
        operation.getTrait(HttpRequestTestsTrait.class).ifPresent(trait -> {
            for (HttpRequestTestCase testCase : trait.getTestCasesFor(implementation)) {
                onlyIfProtocolMatches(testCase, () -> generateRequestTest(testCase));
            }
        });

        // Response Tests
        operation.getTrait(HttpResponseTestsTrait.class).ifPresent(trait -> {
            for (HttpResponseTestCase testCase : trait.getTestCasesFor(implementation)) {
                onlyIfProtocolMatches(testCase, () -> generateResponseTest(testCase));
            }
        });

        // Error Tests
        // 3. Generate test cases for each error on each operation.
        for (StructureShape error : operationIndex.getErrors(operation, service)) {
            if (!error.hasTag("server-only")) {
                error.getTrait(HttpResponseTestsTrait.class).ifPresent(trait -> {
                    for (HttpResponseTestCase testCase : trait.getTestCasesFor(implementation)) {
                        onlyIfProtocolMatches(testCase,
                                () -> generateErrorResponseTest(operation, error, testCase));
                    }
                });
            }
        }
    }

    private void generateRequestTest(HttpRequestTestCase testCase) {
        // TODO: Generate the real request test logic, add logic for skipping
        writeTestBlock(testCase, testCase.getId(), false, () -> {
            writer.write("pass");
        });
    }

    private void generateResponseTest(HttpResponseTestCase testCase) {
        // TODO: Generate the real response test logic, add logic for skipping
        writeTestBlock(testCase, testCase.getId(), true, () -> {
            writer.write("pass");
        });
    }

    private void generateErrorResponseTest(
            OperationShape operation,
            StructureShape error,
            HttpResponseTestCase testCase) {
        // TODO: Generate the real error response test logic, add logic for skipping
        writeTestBlock(testCase,
                String.format("%s_error_%s", testCase.getId(), operation.getId().getName()),
                false,
                () -> {
            writer.write("pass");
        });
    }

    // Only generate test cases when protocol matches the target protocol.
    private <T extends HttpMessageTestCase> void onlyIfProtocolMatches(T testCase, Runnable runnable) {
        if (testCase.getProtocol().equals(protocol)) {
            LOGGER.fine(() -> String.format("Generating protocol test case for %s.%s",
                    service.getId(),
                    testCase.getId())
            );
            runnable.run();
        }
    }

    // write the test block, which may include certain decorators (i.e. `skip`)
    private void writeTestBlock(
            HttpMessageTestCase testCase,
            String testName,
            boolean shouldSkip,
            Runnable f
    ) {
        LOGGER.fine(String.format("Writing test block for %s", testName));

        // Skipped tests are still generated, just not run.
        if (shouldSkip) {
            LOGGER.fine(String.format("Marking test (%s) as skipped.", testName));
            writer.addDependency(SmithyPythonDependency.PYTEST);
            writer.addImport(SmithyPythonDependency.PYTEST.packageName(), "mark", "mark");
            writer.write("@mark.skip()");
        }
        writer.openBlock("async def test_$L():", "", CaseUtils.toSnakeCase(testName), () -> {
            testCase.getDocumentation().ifPresent(writer::writeDocs);
            f.run();
        });
    }
}
