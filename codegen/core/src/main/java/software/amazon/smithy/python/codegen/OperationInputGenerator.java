/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/** Keeps operation declarations, model construction, and generated callers in agreement. */
final class OperationInputGenerator {

    /**
     * The only names a generated operation method binds that a modeled member could plausibly
     * take: {@code self} and the {@code plugins} control parameter.
     *
     * <p>Every other name the operation body binds or references is either underscore-prefixed
     * ({@code _input}, {@code _config}, {@code _pipeline}, the imported {@code _deepcopy} and
     * plugin aliases) or not spelled like a member name, which is always snake case
     * ({@code Plugin}, {@code ClientCall}, the operation schema constant). Template authors
     * must keep it that way: a new lowercase local in the operation body needs a leading
     * underscore, not an entry here, because entries here change the client's public API.
     */
    private static final Set<String> RESERVED = Set.of("self", "plugins");

    private final GenerationContext context;
    private final StructureShape input;
    private final Map<MemberShape, String> parameters = new LinkedHashMap<>();

    OperationInputGenerator(GenerationContext context, OperationShape operation) {
        this.context = context;
        input = context.model().expectShape(operation.getInputShape(), StructureShape.class);
        var members = input.members().stream().filter(member -> {
            var target = context.model().expectShape(member.getTarget());
            return !(target.isUnionShape() && target.hasTrait(StreamingTrait.class));
        }).toList();
        var claimedBy = new HashMap<String, MemberShape>();
        for (var member : members) {
            var name = parameterName(context.symbolProvider().toMemberName(member));
            var previous = claimedBy.put(name, member);
            if (previous != null) {
                // Two members of the same shape normalize to one Python name, so one would
                // silently overwrite the other. This breaks the dataclass too, but the
                // operation method is where it's cheapest to say so.
                throw new CodegenException(String.format(
                        "Members `%s` and `%s` of %s both become the parameter `%s` of operation %s.",
                        previous.getMemberName(),
                        member.getMemberName(),
                        input.getId(),
                        name,
                        operation.getId()));
            }
            parameters.put(member, name);
        }
    }

    /**
     * Maps a member's Python name to the keyword the operation method accepts for it.
     *
     * <p>This is a pure function of the member's own name, so adding a member to a shape
     * can never rename another member's keyword. The mapping is injective: an escaped name
     * always satisfies the escape condition itself, so it can never equal an unescaped one.
     */
    // Package-private for testing.
    static String parameterName(String memberName) {
        // Stripping trailing underscores keeps the escape closed, so `plugins` becomes
        // `plugins_` without stealing the keyword an existing `plugins_` member owns.
        var stem = memberName;
        while (stem.endsWith("_")) {
            stem = stem.substring(0, stem.length() - 1);
        }
        if (RESERVED.contains(stem) || memberName.startsWith("_")) {
            return memberName + "_";
        }
        return memberName;
    }

    void writeParameters(PythonWriter writer) {
        writer.write("self,\n*,");
        var index = NullableIndex.of(context.model());
        parameters.forEach((member, name) -> {
            var type = context.symbolProvider().toSymbol(member);
            if (CodegenUtils.isRequiredMember(index, member)) {
                writer.write("$L: $T,", name, type);
            } else if (member.hasTrait(DefaultTrait.class) && !MemberDefault.usesFactory(context, member)) {
                var value = MemberDefault.of(context, writer, member);
                writer.write("$L: $T$L = $L,",
                        name,
                        type,
                        value.nullable() ? " | None" : "",
                        value.value());
            } else {
                // A member with a mutable default is declared like an omitted member.
                // The modeled default can't be shared between calls, so it's built in
                // the method body when the caller leaves it out.
                writer.write("$L: $T | None = None,", name, type);
            }
        });
        writer.write("plugins: list[$T] | None = None,", CodegenUtils.getPluginSymbol(context.settings()));
    }

    void writeInput(PythonWriter writer) {
        parameters.forEach((member, name) -> {
            if (member.hasTrait(DefaultTrait.class) && MemberDefault.usesFactory(context, member)) {
                writer.write("""
                        if $1L is None:
                            $1L = $2L
                        """, name, MemberDefault.of(context, writer, member).value());
            }
        });
        writer.write("_input = $T(", context.symbolProvider().toSymbol(input)).indent();
        parameters.forEach((member, name) -> writer.write("$L=$L,",
                context.symbolProvider().toMemberName(member),
                name));
        writer.dedent().write(")");
    }

    /**
     * Writes the whole {@code Args:} body, including the {@code plugins} control parameter.
     *
     * <p>{@code plugins} lives here rather than in the caller's template so that this is
     * never empty, which would leave a stray blank line under {@code Args:}.
     */
    void writeDocs(PythonWriter writer) {
        parameters.forEach((member, name) -> {
            // Undocumented members are left out entirely. Restating the name the reader
            // just read is worse than an absence, because it looks like documentation.
            member.getMemberTrait(context.model(), DocumentationTrait.class).ifPresent(docs -> {
                writer.write("$L:", name).indent();
                writer.write("${L|}", writer.formatDocs(docs.getValue(), context));
                writer.dedent();
            });
        });
        writer.write("""
                plugins:
                    A list of callables that modify the configuration dynamically.
                    Changes made by these plugins only apply for the duration of the
                    operation execution and will not affect any other operation
                    invocations.""");
    }

    /** Writes one member's value as the right-hand side of a keyword argument. */
    @FunctionalInterface
    interface MemberValueWriter {
        void write(PythonWriter writer, MemberShape member, Node value);
    }

    /**
     * Writes the keyword arguments that pass {@code values} to this operation.
     *
     * <p>Members {@code values} says nothing about are omitted rather than passed
     * explicitly, so the call exercises the same defaulting an ordinary caller gets.
     */
    void writeArguments(PythonWriter writer, ObjectNode values, MemberValueWriter valueWriter) {
        parameters.forEach((member, name) -> values.getMember(member.getMemberName())
                .ifPresent(value -> writer.write("$L=$C,",
                        name,
                        (Runnable) () -> valueWriter.write(writer, member, value))));
    }
}
