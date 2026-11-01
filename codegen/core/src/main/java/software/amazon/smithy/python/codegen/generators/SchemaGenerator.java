/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import software.amazon.smithy.codegen.core.TopologicalIndex;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.loader.Prelude;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.InputTrait;
import software.amazon.smithy.model.traits.OutputTrait;
import software.amazon.smithy.model.traits.UnitTypeTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SchemaTraitFilterIndex;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Generates compact, tuple-encoded schemas for shapes.
 *
 * <p>Each shape is emitted as pure data: a module global bound to a positional tuple
 * led by its {@link ShapeType} integer (see {@code smithy_core._schema_compact}).
 * Repeated strings are interned into short module constants, prelude member targets
 * collapse to their type integer, and valueless two-state traits collapse into a
 * single integer bit-vector. Nothing is materialized at import; generated code calls
 * {@code hydrate(TUPLE)} to build the real {@code Schema} on first use. A member
 * target that points at a shape not yet defined in file order is emitted as a
 * {@code lambda} so the forward/recursive reference resolves lazily.
 */
@SmithyUnstableApi
public final class SchemaGenerator implements Consumer<Shape> {

    private static final int SCHEMA_PARTITION_SIZE = 50;

    // Bit index -> trait id. MUST match smithy_core._schema_compact._TRAIT_BITS.
    private static final List<String> TRAIT_BITS = List.of(
            "smithy.api#required",
            "smithy.api#idempotencyToken",
            "smithy.api#sensitive",
            "smithy.api#httpLabel",
            "smithy.api#httpPayload",
            "smithy.api#idempotent",
            "smithy.api#sparse",
            "smithy.api#httpResponseCode",
            "smithy.api#hostLabel",
            "smithy.api#requiresLength",
            "smithy.api#httpQueryParams",
            "smithy.api#notProperty");

    // Prelude shape id -> its ShapeType integer substitute. Matches _PRELUDE.
    private static final Map<String, Integer> PRELUDE_INTS = Map.ofEntries(
            Map.entry("smithy.api#Blob", 1),
            Map.entry("smithy.api#Boolean", 2),
            Map.entry("smithy.api#String", 3),
            Map.entry("smithy.api#Timestamp", 4),
            Map.entry("smithy.api#Byte", 5),
            Map.entry("smithy.api#Short", 6),
            Map.entry("smithy.api#Integer", 7),
            Map.entry("smithy.api#Long", 8),
            Map.entry("smithy.api#Float", 9),
            Map.entry("smithy.api#Double", 10),
            Map.entry("smithy.api#BigInteger", 11),
            Map.entry("smithy.api#BigDecimal", 12),
            Map.entry("smithy.api#Document", 13),
            Map.entry("smithy.api#PrimitiveBoolean", 2),
            Map.entry("smithy.api#PrimitiveByte", 5),
            Map.entry("smithy.api#PrimitiveShort", 6),
            Map.entry("smithy.api#PrimitiveInteger", 7),
            Map.entry("smithy.api#PrimitiveLong", 8),
            Map.entry("smithy.api#PrimitiveFloat", 9),
            Map.entry("smithy.api#PrimitiveDouble", 10));

    private static final int UNIT_INT = -1;

    private final GenerationContext context;

    // Shapes already emitted in file order; a target not yet here is a forward ref.
    private final Set<ShapeId> written = new HashSet<>();
    private Set<ShapeId> localShapes = Set.of();
    private boolean partitioned;

    // Interned string -> short constant symbol (StringStore).
    private final Map<String, String> stringStore = new LinkedHashMap<>();

    // Variable names already handed out, for collision detection across both the
    // initialism and preferred-prefix allocation paths.
    private final Set<String> allocated = new HashSet<>();

    public SchemaGenerator(GenerationContext context) {
        this.context = context;
    }

    @Override
    public void accept(Shape shape) {
        // Collection happens in generateAll's single pass.
    }

    public static void generateAll(
            GenerationContext context,
            Collection<Shape> shapes,
            Function<Shape, Boolean> filter
    ) {
        var generator = new SchemaGenerator(context);
        var index = TopologicalIndex.of(context.model());
        var ordered = Stream.concat(
                index.getOrderedShapes().stream(),
                index.getRecursiveShapes().stream())
                .filter(shapes::contains)
                .filter(shape -> !shape.isResourceShape()
                        && !shape.isMemberShape()
                        && !Prelude.isPreludeShape(shape))
                .filter(filter::apply)
                .collect(Collectors.toList());
        generator.writeFile(ordered);
    }

    public static void generateAll(GenerationContext context, Collection<Shape> shapes) {
        SchemaGenerator.generateAll(context, shapes, s -> true);
    }

    private void writeFile(List<Shape> shapes) {
        for (var shape : shapes) {
            intern(shape.getId().getNamespace(), "n");
            intern(shape.getId().getName());
            internTraitStrings(filterTraits(shape));
            for (var member : shape.members()) {
                intern(member.getMemberName());
                internTraitStrings(filterTraits(member));
            }
        }

        var module = context.settings().moduleName();
        var filename = String.format("src/%s/_private/schemas.py", module);
        var namespace = String.format("%s._private.schemas", module);
        if (shapes.size() <= SCHEMA_PARTITION_SIZE) {
            writeSchemaModule(filename, namespace, shapes, false);
            return;
        }

        var partitions = partitionSchemas(shapes);
        context.writerDelegator().useFileWriter(filename, namespace, writer -> writeFacade(writer, partitions));
        for (int i = 0; i < partitions.size(); i++) {
            var partitionFilename = String.format("src/%s/_private/schemas_%d.py", module, i);
            var partitionNamespace = String.format("%s._private.schemas_%d", module, i);
            writeSchemaModule(partitionFilename, partitionNamespace, partitions.get(i), true);
        }
    }

    private void writeSchemaModule(
            String filename,
            String namespace,
            List<Shape> shapes,
            boolean isPartitioned
    ) {
        var ids = shapes.stream().map(Shape::getId).collect(Collectors.toSet());
        context.writerDelegator().useFileWriter(filename, namespace, writer -> {
            if (isPartitioned && shapes.stream()
                    .flatMap(shape -> references(shape).stream())
                    .anyMatch(target -> !ids.contains(target)
                            && !isInlineSchemaReference(target))) {
                writer.addImport(context.settings().moduleName() + "._private", "schemas");
            }

            writeStringStore(writer, schemaStrings(shapes));
            written.clear();
            localShapes = ids;
            partitioned = isPartitioned;
            for (var shape : shapes) {
                writeShape(writer, shape);
            }
            localShapes = Set.of();
            partitioned = false;
        });
    }

    private void writeFacade(PythonWriter writer, List<List<Shape>> partitions) {
        writer.addStdlibImport("importlib", "import_module");
        writer.openBlock("_PARTITION_NAMES: tuple[tuple[str, ...], ...] = (", ")", () -> {
            for (var shapes : partitions) {
                writer.openBlock("(", "),", () -> {
                    for (var shape : shapes) {
                        writer.write("$S,", schemaName(shape));
                    }
                });
            }
        });
        writer.write("""
                _PARTITIONS = {
                    name: index
                    for index, names in enumerate(_PARTITION_NAMES)
                    for name in names
                }
                __all__ = list(_PARTITIONS)  # pyright: ignore[reportUnsupportedDunderAll]
                del _PARTITION_NAMES
                """);
        writer.write("""
                def __getattr__(name: str):
                    try:
                        partition = _PARTITIONS[name]
                    except KeyError as error:
                        raise AttributeError(name) from error
                    module = import_module(f".schemas_{partition}", __package__)
                    value = getattr(module, name)
                    globals()[name] = value
                    return value


                def __dir__() -> list[str]:
                    return sorted({*globals(), *__all__})
                """);
    }

    private List<List<Shape>> partitionSchemas(List<Shape> shapes) {
        var groups = recursiveGroups(shapes);
        var countPartitions = new ArrayList<List<Shape>>();
        var current = new ArrayList<Shape>();
        for (var group : groups) {
            if (!current.isEmpty() && current.size() + group.size() > SCHEMA_PARTITION_SIZE) {
                countPartitions.add(List.copyOf(current));
                current.clear();
            }
            current.addAll(group);
        }
        if (!current.isEmpty()) {
            countPartitions.add(List.copyOf(current));
        }
        var partitionCount = countPartitions.size();
        if (partitionCount < 2) {
            return countPartitions;
        }

        var weights = groups.stream().mapToLong(this::schemaGroupWeight).toArray();
        var partitions = new ArrayList<List<Shape>>(partitionCount);
        int start = 0;
        long remainingWeight = Arrays.stream(weights).sum();
        for (int remainingParts = partitionCount; remainingParts > 1; remainingParts--) {
            double target = (double) remainingWeight / remainingParts;
            int end = start;
            long weight = 0;
            int lastEnd = groups.size() - remainingParts + 1;
            while (end < lastEnd) {
                long nextWeight = weight + weights[end];
                if (weight > 0 && Math.abs(target - weight) <= Math.abs(target - nextWeight)) {
                    break;
                }
                weight = nextWeight;
                end++;
            }
            partitions.add(flatten(groups.subList(start, end)));
            start = end;
            remainingWeight -= weight;
        }
        partitions.add(flatten(groups.subList(start, groups.size())));
        return partitions;
    }

    private List<List<Shape>> recursiveGroups(List<Shape> shapes) {
        var byId = shapes.stream()
                .collect(Collectors.toMap(
                        Shape::getId,
                        Function.identity(),
                        (left, right) -> left,
                        LinkedHashMap::new));
        var positions = new HashMap<ShapeId, Integer>();
        var graph = new LinkedHashMap<ShapeId, List<ShapeId>>();
        var reverse = new LinkedHashMap<ShapeId, List<ShapeId>>();
        for (int i = 0; i < shapes.size(); i++) {
            var id = shapes.get(i).getId();
            positions.put(id, i);
            reverse.put(id, new ArrayList<>());
        }
        for (var shape : shapes) {
            var targets = references(shape).stream().filter(byId::containsKey).toList();
            graph.put(shape.getId(), targets);
            for (var target : targets) {
                reverse.get(target).add(shape.getId());
            }
        }

        var finished = new ArrayList<ShapeId>();
        var visited = new HashSet<ShapeId>();
        for (var root : graph.keySet()) {
            if (!visited.add(root)) {
                continue;
            }
            var pending = new ArrayDeque<SearchFrame>();
            pending.push(new SearchFrame(root, 0));
            while (!pending.isEmpty()) {
                var frame = pending.pop();
                var targets = graph.get(frame.id());
                if (frame.nextTarget() == targets.size()) {
                    finished.add(frame.id());
                    continue;
                }
                pending.push(new SearchFrame(frame.id(), frame.nextTarget() + 1));
                var target = targets.get(frame.nextTarget());
                if (visited.add(target)) {
                    pending.push(new SearchFrame(target, 0));
                }
            }
        }

        var recursiveComponents = new HashMap<ShapeId, List<ShapeId>>();
        visited.clear();
        Collections.reverse(finished);
        for (var root : finished) {
            if (!visited.add(root)) {
                continue;
            }
            var component = new ArrayList<ShapeId>();
            var pending = new ArrayDeque<ShapeId>();
            pending.push(root);
            while (!pending.isEmpty()) {
                var current = pending.pop();
                component.add(current);
                for (var target : reverse.get(current)) {
                    if (visited.add(target)) {
                        pending.push(target);
                    }
                }
            }
            if (component.size() > 1 || graph.get(root).contains(root)) {
                component.sort((left, right) -> Integer.compare(positions.get(left), positions.get(right)));
                var immutable = List.copyOf(component);
                for (var id : component) {
                    recursiveComponents.put(id, immutable);
                }
            }
        }

        var groups = new ArrayList<List<Shape>>();
        var grouped = new HashSet<ShapeId>();
        for (var shape : shapes) {
            if (grouped.contains(shape.getId())) {
                continue;
            }
            var component = recursiveComponents.getOrDefault(shape.getId(), List.of(shape.getId()));
            groups.add(component.stream().map(byId::get).toList());
            grouped.addAll(component);
        }
        return groups;
    }

    private List<ShapeId> references(Shape shape) {
        var references = new LinkedHashSet<ShapeId>();
        for (var member : shape.members()) {
            references.add(member.getTarget());
        }
        shape.asOperationShape().ifPresent(operation -> {
            references.add(operation.getInputShape());
            references.add(operation.getOutputShape());
            references.addAll(operation.getErrors());
        });
        return List.copyOf(references);
    }

    private List<Shape> flatten(List<List<Shape>> groups) {
        return groups.stream().flatMap(Collection::stream).toList();
    }

    private long schemaGroupWeight(List<Shape> group) {
        long declarations = schemaStrings(group).stream()
                .mapToLong(value -> stringStore.get(value).length() + value.length() + 4L)
                .sum();
        return declarations + group.stream().mapToLong(this::schemaShapeWeight).sum();
    }

    private long schemaShapeWeight(Shape shape) {
        long weight = 60L
                + shape.getId().getNamespace().length()
                + 2L * shape.getId().getName().length()
                + traitsWeight(filterTraits(shape));
        for (var member : shape.members()) {
            weight += 40L
                    + 2L * member.getMemberName().length()
                    + schemaReferenceWeight(member.getTarget())
                    + traitsWeight(filterTraits(member));
        }
        if (shape.isOperationShape()) {
            var operation = shape.asOperationShape().orElseThrow();
            weight += schemaReferenceWeight(operation.getInputShape());
            weight += schemaReferenceWeight(operation.getOutputShape());
            for (var error : operation.getErrors()) {
                weight += schemaReferenceWeight(error);
            }
        }
        return weight;
    }

    private long schemaReferenceWeight(ShapeId target) {
        return isInlineSchemaReference(target)
                ? 4L
                : schemaName(context.model().expectShape(target)).length();
    }

    private boolean isInlineSchemaReference(ShapeId target) {
        return target.equals(UnitTypeTrait.UNIT) || PRELUDE_INTS.containsKey(target.toString());
    }

    private long traitsWeight(Map<ShapeId, Optional<Node>> traits) {
        long weight = 2;
        for (var entry : traits.entrySet()) {
            weight += stringStore.get(entry.getKey().toString()).length() + 4L;
            if (entry.getValue().isPresent()) {
                var value = entry.getValue().get();
                weight += value.isStringNode()
                        ? stringStore.get(value.expectStringNode().getValue()).length()
                        : value.toString().length();
            }
        }
        return weight;
    }

    private Set<String> schemaStrings(Collection<Shape> shapes) {
        var values = new HashSet<String>();
        for (var shape : shapes) {
            values.add(shape.getId().getNamespace());
            values.add(shape.getId().getName());
            collectTraitStrings(values, filterTraits(shape));
            for (var member : shape.members()) {
                values.add(member.getMemberName());
                collectTraitStrings(values, filterTraits(member));
            }
        }
        return values;
    }

    private void collectTraitStrings(Set<String> values, Map<ShapeId, Optional<Node>> traits) {
        for (var entry : traits.entrySet()) {
            values.add(entry.getKey().toString());
            entry.getValue()
                    .filter(Node::isStringNode)
                    .map(Node::expectStringNode)
                    .map(node -> node.getValue())
                    .ifPresent(values::add);
        }
    }

    private record SearchFrame(ShapeId id, int nextTarget) {}

    // String interning follows smithy-typescript's StringStore: a general literal
    // becomes `_` + its initials (uppercase/word-start letters), deconflicted with its
    // remaining letters; namespaces use a preferred `n{N}` prefix since they repeat
    // heavily and carry no useful initials.
    private String intern(String value) {
        return stringStore.computeIfAbsent(value, this::allocateVariable);
    }

    private String intern(String value, String preferredPrefix) {
        return stringStore.computeIfAbsent(value, v -> assignPreferredKey(v, preferredPrefix));
    }

    private String assignPreferredKey(String literal, String preferredPrefix) {
        int suffix = 0;
        var candidate = preferredPrefix + suffix;
        while (allocated.contains(candidate)) {
            candidate = preferredPrefix + (++suffix);
        }
        allocated.add(candidate);
        return candidate;
    }

    // Mirrors StringStore.allocateVariable: initials from word-split sections, or the
    // uppercase (and leading, while still neutral) letters of a single CamelCase word,
    // with the rest queued to break collisions.
    private String allocateVariable(String literal) {
        var sections = Arrays.stream(literal.split("[-_\\s]"))
                .filter(s -> !s.isEmpty())
                .toArray(String[]::new);
        var v = new StringBuilder("_");
        var deconfliction = new ArrayDeque<Character>();
        if (sections.length > 1) {
            for (var s : sections) {
                char c = s.charAt(0);
                if (isAllowedChar(c)) {
                    v.append(c);
                }
            }
        } else {
            for (int i = 0; i < literal.length(); i++) {
                char c = literal.charAt(i);
                if ((c >= 'A' && c <= 'Z') || (isNeutral(v.toString()) && isAllowedChar(c))) {
                    v.append(c);
                } else if (isAllowedChar(c)) {
                    deconfliction.add(c);
                }
            }
        }
        if (v.length() == 1) {
            v.append("v");
        }
        while (allocated.contains(v.toString())) {
            v.append(deconfliction.isEmpty() ? '_' : deconfliction.poll());
        }
        allocated.add(v.toString());
        return v.toString();
    }

    private boolean isAllowedChar(char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    private boolean isNeutral(String variable) {
        for (int i = 0; i < variable.length(); i++) {
            if (variable.charAt(i) != '_') {
                return false;
            }
        }
        return true;
    }

    private void internTraitStrings(Map<ShapeId, Optional<Node>> traits) {
        for (var entry : traits.entrySet()) {
            intern(entry.getKey().toString());
            var value = entry.getValue();
            if (value.isPresent() && value.get().isStringNode()) {
                intern(value.get().expectStringNode().getValue());
            }
        }
    }

    private void writeStringStore(PythonWriter writer, Set<String> values) {
        for (var entry : stringStore.entrySet()) {
            if (values.contains(entry.getKey())) {
                writer.write("$L = $S", entry.getValue(), entry.getKey());
            }
        }
        writer.write("");
    }

    private void writeShape(PythonWriter writer, Shape shape) {
        var nsConst = stringStore.get(shape.getId().getNamespace());
        var nameConst = stringStore.get(shape.getId().getName());
        var traits = filterTraits(shape);
        int typeInt = typeInt(shape);
        var key = schemaName(shape);

        // Annotate the global with its static-schema alias so a forward/recursive
        // lambda member doesn't leave the inferred tuple type partially unknown, which
        // otherwise leaks to every import and APIOperation(static_schema=) call site.
        var typeSymbol = shape.isOperationShape()
                ? RuntimeTypes.STATIC_OPERATION_SCHEMA
                : RuntimeTypes.STATIC_SCHEMA;
        writer.write("$L: $T = (", key, typeSymbol);
        writer.writeInline("$L, $L, $L, ", Integer.toString(typeInt), nsConst, nameConst);
        writeTraits(writer, traits);

        if (shape.isOperationShape()) {
            writeOperationRefs(writer, shape.asOperationShape().get());
            writer.write(")");
            writer.write("");
            written.add(shape.getId());
            return;
        }

        if (shape.members().isEmpty()) {
            writer.write(")");
            writer.write("");
            written.add(shape.getId());
            return;
        }

        writer.write(",");
        writer.write("($L),", memberNameTuple(shape));
        writer.openBlock("(", "),", () -> writeMemberTargets(writer, shape));
        writer.write(")");
        writer.write("");
        written.add(shape.getId());
    }

    // Operation tuple trailing slots: input_ref, output_ref, (error_refs...). Matches
    // _schema_compact._OP_INPUT / _OP_OUTPUT / _OP_ERRORS.
    private void writeOperationRefs(PythonWriter writer, OperationShape op) {
        writer.write(",");
        writeOperationRef(writer, op.getInputShape());
        writeOperationRef(writer, op.getOutputShape());
        writer.openBlock("(", ")", () -> {
            for (var error : op.getErrors()) {
                writer.writeInline("");
                writeSchemaRef(writer, error);
                writer.write(",");
            }
        });
    }

    private void writeOperationRef(PythonWriter writer, ShapeId target) {
        writer.writeInline("");
        writeSchemaRef(writer, target);
        writer.write(",");
    }

    private String schemaName(Shape shape) {
        return context.symbolProvider()
                .toSymbol(shape)
                .expectProperty(SymbolProperties.SCHEMA)
                .getSymbol()
                .getName();
    }

    private String memberNameTuple(Shape shape) {
        var names = new ArrayList<String>();
        for (var member : shape.members()) {
            names.add(stringStore.get(member.getMemberName()));
        }
        return names.isEmpty() ? "" : String.join(", ", names) + ",";
    }

    private void writeMemberTargets(PythonWriter writer, Shape shape) {
        for (var member : shape.members()) {
            writer.writeInline("");
            writeMemberTarget(writer, member);
            writer.write(",");
        }
    }

    private void writeMemberTarget(PythonWriter writer, MemberShape member) {
        var memberTraits = filterTraits(member);
        writer.writeInline("(");
        writeSchemaRef(writer, member.getTarget());
        writer.writeInline(", ");
        writeTraits(writer, memberTraits);
        writer.writeInline(")");
    }

    // Emits a reference to another shape's schema: a prelude int / UNIT sentinel, a
    // bare sibling symbol when already defined above (folds as a constant), else a
    // lambda for a forward or recursive reference.
    private void writeSchemaRef(PythonWriter writer, ShapeId target) {
        if (target.equals(UnitTypeTrait.UNIT)) {
            writer.writeInline("$L", Integer.toString(UNIT_INT));
            return;
        }
        if (PRELUDE_INTS.containsKey(target.toString())) {
            writer.writeInline("$L", Integer.toString(PRELUDE_INTS.get(target.toString())));
            return;
        }
        var targetName = schemaName(context.model().expectShape(target));
        if (partitioned && !localShapes.contains(target)) {
            writer.writeInline("lambda: schemas.$L", targetName);
            return;
        }
        if (written.contains(target)) {
            writer.writeInline("$L", targetName);
        } else {
            writer.writeInline("lambda: $L", targetName);
        }
    }

    /**
     * Writes the compact trait literal: an int bit-vector when every trait is a
     * valueless two-state trait, otherwise a dict of interned id -> value (also
     * carrying any valueless traits present).
     */
    private void writeTraits(PythonWriter writer, Map<ShapeId, Optional<Node>> traits) {
        if (traits.isEmpty()) {
            writer.writeInline("0");
            return;
        }

        int bits = 0;
        var valued = new LinkedHashMap<ShapeId, Optional<Node>>();
        var valuelessKnown = new ArrayList<String>();
        for (var entry : traits.entrySet()) {
            var id = entry.getKey().toString();
            int bitIndex = TRAIT_BITS.indexOf(id);
            if (bitIndex >= 0 && entry.getValue().isEmpty()) {
                bits |= (1 << bitIndex);
                valuelessKnown.add(id);
            } else {
                valued.put(entry.getKey(), entry.getValue());
            }
        }

        if (valued.isEmpty()) {
            writer.writeInline("$L", Integer.toString(bits));
            return;
        }

        writer.writeInline("{");
        boolean first = true;
        for (var entry : valued.entrySet()) {
            if (!first) {
                writer.writeInline(", ");
            }
            first = false;
            writer.writeInline("$L: ", stringStore.get(entry.getKey().toString()));
            if (entry.getValue().isEmpty()) {
                writer.writeInline("None");
            } else if (entry.getValue().get().isStringNode()) {
                writer.writeInline("$L", stringStore.get(entry.getValue().get().expectStringNode().getValue()));
            } else {
                writer.writeInline("$N", entry.getValue().get());
            }
        }
        for (var id : valuelessKnown) {
            writer.writeInline(", $L: None", stringStore.get(id));
        }
        writer.writeInline("}");
    }

    private Map<ShapeId, Optional<Node>> filterTraits(Shape shape) {
        var traitFilter = SchemaTraitFilterIndex.of(context.model());
        Map<ShapeId, Optional<Node>> filtered = new LinkedHashMap<>();
        for (var entry : shape.getAllTraits().entrySet()) {
            if (!traitFilter.includeTrait(entry.getKey())) {
                continue;
            }
            var value = entry.getValue().toNode();
            // An empty-object trait value normally means a valueless annotation trait, so
            // it collapses to Optional.empty(). @default is exempt: `@default({})` and
            // `@default([])` are real document values the runtime must rebuild, distinct
            // from `@default(null)`.
            if (value.isObjectNode()
                    && value.asObjectNode().get().getMembers().isEmpty()
                    && !entry.getKey().equals(DefaultTrait.ID)) {
                filtered.put(entry.getKey(), Optional.empty());
            } else {
                filtered.put(entry.getKey(), Optional.of(value));
            }
        }
        // Record the generator's own input/output nullability decision explicitly on
        // the schema: OperationIndex treats operation I/O structures as @input/@output
        // regardless of an authored trait, so the runtime reads one authoritative
        // signal instead of reconstructing the operation graph.
        if (shape.isStructureShape()) {
            var operationIndex = OperationIndex.of(context.model());
            if (operationIndex.isInputStructure(shape)) {
                filtered.put(InputTrait.ID, Optional.empty());
            }
            if (operationIndex.isOutputStructure(shape)) {
                filtered.put(OutputTrait.ID, Optional.empty());
            }
        }
        return filtered;
    }

    private int typeInt(Shape shape) {
        return switch (shape.getType()) {
            case BLOB -> 1;
            case BOOLEAN -> 2;
            case STRING -> 3;
            case TIMESTAMP -> 4;
            case BYTE -> 5;
            case SHORT -> 6;
            case INTEGER -> 7;
            case LONG -> 8;
            case FLOAT -> 9;
            case DOUBLE -> 10;
            case BIG_INTEGER -> 11;
            case BIG_DECIMAL -> 12;
            case DOCUMENT -> 13;
            case ENUM -> 14;
            case INT_ENUM -> 15;
            case LIST, SET -> 16;
            case MAP -> 17;
            case STRUCTURE -> 18;
            case UNION -> 19;
            case SERVICE -> 21;
            case OPERATION -> 23;
            default -> 3;
        };
    }
}
