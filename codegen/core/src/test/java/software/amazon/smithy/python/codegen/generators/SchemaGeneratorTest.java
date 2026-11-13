/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.shapes.ShapeId;

public class SchemaGeneratorTest {

    @Test
    public void movesSharedShapesTowardRelatedOperations() {
        var create = ShapeId.from("example.affinity#Create");
        var describe = ShapeId.from("example.affinity#Describe");
        var unrelated = ShapeId.from("example.affinity#Unrelated");

        var optimized = SchemaGenerator.improveOperationAffinityLayout(
                List.of(1, 1, 1, 1),
                new long[] {5, 5, 10, 5},
                List.of(
                        Set.of(create),
                        Set.of(create, describe),
                        Set.of(unrelated),
                        Set.of(describe)),
                List.of(
                        List.of(0),
                        List.of(1, 2),
                        List.of(3)),
                2);

        assertEquals(
                List.of(
                        List.of(0, 1),
                        List.of(2),
                        List.of(3)),
                optimized);
    }

    @Test
    public void operationIterationOrderDoesNotChangeLayout() {
        var create = ShapeId.from("example.affinity#Create");
        var describe = ShapeId.from("example.affinity#Describe");
        var update = ShapeId.from("example.affinity#Update");
        var shapeCounts = List.of(1, 1, 1, 1, 1);
        var weights = new long[] {5, 5, 5, 5, 5};
        var initialLayout = List.of(
                List.of(0, 1),
                List.of(2, 3),
                List.of(4));

        var forward = SchemaGenerator.improveOperationAffinityLayout(
                shapeCounts,
                weights,
                List.of(
                        orderedSet(create, describe),
                        orderedSet(update),
                        orderedSet(describe, create),
                        orderedSet(describe, update),
                        orderedSet(update, create)),
                initialLayout,
                2);
        var reversed = SchemaGenerator.improveOperationAffinityLayout(
                shapeCounts,
                weights,
                List.of(
                        orderedSet(describe, create),
                        orderedSet(update),
                        orderedSet(create, describe),
                        orderedSet(update, describe),
                        orderedSet(create, update)),
                initialLayout,
                2);

        assertEquals(forward, reversed);
    }

    private static Set<ShapeId> orderedSet(ShapeId... values) {
        return new LinkedHashSet<>(List.of(values));
    }
}
