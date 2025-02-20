/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.loader.Prelude;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumTrait;
import software.amazon.smithy.model.traits.UnitTypeTrait;
import software.amazon.smithy.model.traits.synthetic.SyntheticEnumTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Generates schemas for shapes.
 *
 * <p>Schemas are essentially a reduced, runtime-available model.
 */
@SmithyUnstableApi
public final class SchemaGenerator implements Consumer<Shape> {
    private static final Logger LOGGER = Logger.getLogger(SchemaGenerator.class.getName());

    // Filter out traits that would overly bloat the definition, which are already part of the
    // class, such as documentation.
    private static final Set<ShapeId> DEFAULT_TRAIT_FILTER = Set.of(
            DocumentationTrait.ID,
            EnumTrait.ID,
            SyntheticEnumTrait.ID);

    private static final Symbol UNIT_SYMBOL = Symbol.builder()
            .name("UNIT")
            .namespace("smithy_core.prelude", ".")
            .addDependency(SmithyPythonDependency.SMITHY_CORE)
            .build();

    private final GenerationContext context;
    private final Set<ShapeId> generatedShapes = new HashSet<>();
    private final Map<MemberShape, Integer> deferredMembers = new HashMap<>();

    public SchemaGenerator(GenerationContext context) {
        this.context = context;
    }

    @Override
    public void accept(Shape shape) {
        var symbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.SCHEMA).getSymbol();
        context.writerDelegator()
                .useFileWriter(
                        symbol.getDefinitionFile(),
                        symbol.getNamespace(),
                        writer -> writeShapeSchema(writer, shape));
        generatedShapes.add(shape.getId());
    }

    private void writeShapeSchema(PythonWriter writer, Shape shape) {
        writer.addImport("smithy_core.schemas", "Schema");
        writer.addImports("smithy_core.shapes", Set.of("ShapeID", "ShapeType"));
        writer.pushState();

        var symbol = context.symbolProvider().toSymbol(shape).expectProperty(SymbolProperties.SCHEMA).getSymbol();

        var traits = filterTraits(shape);
        writer.putContext("isCollection", shape.isStructureShape() || !shape.members().isEmpty());
        writer.putContext("isStructure", shape.isStructureShape());
        writer.putContext("shapeType", CaseUtils.toSnakeCase(shape.getType().toString()).toUpperCase());
        writer.putContext("hasTraits", !traits.isEmpty());

        writer.write("""
                $L = Schema${?isCollection}.collection${/isCollection}(
                    id=ShapeID($S),
                    ${^isStructure}shape_type=ShapeType.${shapeType:L},${/isStructure}
                    ${?hasTraits}
                    traits=[
                        ${C|}
                    ],
                    ${/hasTraits}
                    ${C|}
                )
                """,
                symbol.getName(),
                shape.getId(),
                writer.consumer(w -> writeTraits(w, traits)),
                writer.consumer(w -> writeSchemaMembers(w, shape)));
        writer.popState();
    }

    private Map<ShapeId, Optional<Node>> filterTraits(Shape shape) {
        return shape.getAllTraits()
                .entrySet()
                .stream()
                .filter(t -> !DEFAULT_TRAIT_FILTER.contains(t.getKey()))
                .collect(Collectors.toMap(Map.Entry::getKey, e -> {
                    var value = e.getValue().toNode();
                    if (value.isObjectNode() && value.asObjectNode().get().getMembers().isEmpty()) {
                        return Optional.empty();
                    }
                    return Optional.of(value);
                }));
    }

    private void writeTraits(PythonWriter writer, Map<ShapeId, Optional<Node>> traits) {
        writer.addImport("smithy_core.traits", "Trait");
        writer.pushState();
        writer.putContext("traits", traits);
        writer.write("""
                ${#traits}
                Trait(id=ShapeID(${key:S})${?value}, value=${value:N}${/value}),
                ${/traits}""");
        writer.popState();
    }

    private void writeSchemaMembers(PythonWriter writer, Shape shape) {
        if (shape.members().isEmpty()) {
            return;
        }

        writer.openBlock("members={", "}", () -> {
            int index = 0;
            for (MemberShape member : shape.members()) {
                if (!generatedShapes.contains(member.getTarget()) && !Prelude.isPreludeShape(member.getTarget())) {
                    deferredMembers.put(member, index++);
                    continue;
                }

                writer.pushState();
                var traits = filterTraits(member);
                writer.putContext("hasTraits", !traits.isEmpty());

                // For some reason the unit shape is being stripped from the model, despite the fact that
                // it's referenced.
                Symbol targetSchemaSymbol;
                if (member.getTarget().equals(UnitTypeTrait.UNIT)) {
                    targetSchemaSymbol = UNIT_SYMBOL;
                } else {
                    var targetSymbol = context.symbolProvider()
                            .toSymbol(context.model().expectShape(member.getTarget()));
                    targetSchemaSymbol = targetSymbol.expectProperty(SymbolProperties.SCHEMA).getSymbol();
                }

                writer.write("""
                        $S: {
                            "target": $T,
                            "index": $L,
                            ${?hasTraits}
                            "traits": [
                                ${C|}
                            ],
                            ${/hasTraits}
                        },
                        """,
                        member.getMemberName(),
                        targetSchemaSymbol,
                        index,
                        writer.consumer(w -> writeTraits(w, traits)));

                index++;
                writer.popState();
            }
        });
    }

    // Some shapes have members that refer to themselves, or members that refer to other
    // shapes that then refer back to them. In typing we can get around that with forward
    // references, but when generating schemas we need to instead defer creating those
    // members until all schemas exist.
    public void finalizeRecursiveShapes() {
        var filename = String.format("%s/_private/schemas.py", context.settings().moduleName());
        var namespace = String.format("%s._private.schemas", context.settings().moduleName());
        context.writerDelegator().useFileWriter(filename, namespace, this::finalizeRecursiveShapes);
    }

    private void finalizeRecursiveShapes(PythonWriter writer) {
        writer.addImport("smithy_core.schemas", "Schema");
        writer.addImport("smithy_core.shapes", "ShapeType");

        for (Map.Entry<MemberShape, Integer> entry : deferredMembers.entrySet()) {
            var member = entry.getKey();
            LOGGER.warning("Generating member: " + member.getId());
            var container = context.symbolProvider()
                    .toSymbol(context.model().expectShape(member.getContainer()))
                    .expectProperty(SymbolProperties.SCHEMA)
                    .getSymbol();
            var target = context.symbolProvider()
                    .toSymbol(context.model().expectShape(member.getTarget()))
                    .expectProperty(SymbolProperties.SCHEMA)
                    .getSymbol();

            writer.pushState();
            var traits = filterTraits(member);
            writer.putContext("hasTraits", !traits.isEmpty());

            writer.write("""
                    $1T.members[$2S] = Schema.member(
                        id=$1T.id.with_member($2S),
                        target=$3T,
                        index=$5L,
                        ${?hasTraits}
                        member_traits=[
                            ${4C|}
                        ],
                        ${/hasTraits}
                    )

                    """,
                    container,
                    member.getMemberName(),
                    target,
                    writer.consumer(w -> writeTraits(w, traits)),
                    entry.getValue());

            writer.popState();
        }

        deferredMembers.clear();
    }
}
