/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import software.amazon.smithy.build.MockManifest;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.PythonSymbolProvider;
import software.amazon.smithy.python.codegen.writer.PythonDelegator;

public class PartitionFilenamesTest {

    @ParameterizedTest
    @ValueSource(ints = {901, 1001, 2501, 10001})
    public void filenamesSortNumericallyAndFacadesMatch(int shapeCount) {
        var service = ServiceShape.builder().id("example#Service").version("1").build();
        var builder = Model.builder().addShape(service);
        var shapes = new ArrayList<Shape>();
        for (int i = 0; i < shapeCount; i++) {
            // Alphabetic suffixes avoid collisions in the schema string store,
            // which ignores digits when allocating variable names.
            var name = new StringBuilder("Shape");
            int index = i;
            do {
                name.append((char) ('A' + index % 26));
                index /= 26;
            } while (index > 0);
            var shape = StructureShape.builder()
                    .id("example#" + name)
                    .addTrait(new DocumentationTrait(""))
                    .build();
            builder.addShape(shape);
            shapes.add(shape);
        }
        var model = builder.build();
        var settings = PythonSettings.builder()
                .service(service.getId())
                .moduleName("example")
                .moduleVersion("1.0.0")
                .build();
        var symbols = new PythonSymbolProvider(model, settings);
        var manifest = new MockManifest();
        var delegator = new PythonDelegator(manifest, symbols, settings);
        var context = GenerationContext.builder()
                .model(model)
                .settings(settings)
                .symbolProvider(symbols)
                .fileManifest(manifest)
                .writerDelegator(delegator)
                .build();
        SchemaGenerator.generateAll(context, shapes);
        new ModelStubGenerator(context, shapes).run();
        delegator.flushWriters();

        var schemas = partitionFiles(manifest, "schemas", ".py");
        var stubs = partitionFiles(manifest, "models", ".pyi");
        assertEquals((shapeCount + 99) / 100, schemas.size());
        assertEquals((shapeCount + 249) / 250, stubs.size());
        assertNumericalOrder(schemas);
        assertNumericalOrder(stubs);
        var width = Integer.toString(schemas.size() - 1).length();
        assertTrue(manifest.expectFileString("src/example/_private/schemas.py")
                .contains("f\".schemas_{partition:0" + width + "d}\""));
        var facade = manifest.expectFileString("src/example/models.pyi");
        for (var stub : stubs) {
            assertTrue(facade.contains("from ._private." + stub.replace(".pyi", "") + " import ("));
        }
    }

    private static List<String> partitionFiles(MockManifest manifest, String prefix, String extension) {
        return manifest.getFiles()
                .stream()
                .map(path -> path.getFileName().toString())
                .filter(name -> name.startsWith(prefix + "_") && name.endsWith(extension))
                .sorted()
                .toList();
    }

    private static void assertNumericalOrder(List<String> files) {
        var numerical = files.stream()
                .sorted(Comparator.comparingInt(PartitionFilenamesTest::partitionIndex))
                .toList();
        assertEquals(numerical, files);
        assertEquals(0, partitionIndex(files.get(0)));
        assertEquals(files.size() - 1, partitionIndex(files.get(files.size() - 1)));
    }

    private static int partitionIndex(String filename) {
        return Integer.parseInt(filename.substring(filename.indexOf('_') + 1, filename.indexOf('.')));
    }
}
