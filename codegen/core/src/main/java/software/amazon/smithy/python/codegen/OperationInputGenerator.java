/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/** Keeps operation declarations, model construction, and generated callers in agreement. */
final class OperationInputGenerator {
    private final GenerationContext context;
    private final StructureShape input;
    private final Map<MemberShape, String> parameters = new LinkedHashMap<>();

    OperationInputGenerator(GenerationContext context, OperationShape operation) {
        this.context = context;
        input = context.model().expectShape(operation.getInputShape(), StructureShape.class);
        // Also avoid reassigning typed parameters to unrelated pipeline locals.
        var reserved = new HashSet<>(Set.of("self",
                "plugins",
                "deepcopy",
                "input",
                "operation_plugins",
                "config",
                "plugin",
                "retry_strategy",
                "pipeline",
                "call"));
        // Integration plugins are referenced inside the method too. A modeled
        // parameter must not shadow one of their imported function names.
        for (var integration : context.integrations()) {
            for (var plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesOperation(context.model(), context.settings().service(context.model()), operation)) {
                    plugin.getPythonPlugin().ifPresent(symbol -> reserved.add(symbol.getAlias()));
                }
            }
        }
        var members = input.members().stream().filter(member -> {
            var target = context.model().expectShape(member.getTarget());
            return !(target.isUnionShape() && target.hasTrait(StreamingTrait.class));
        }).toList();
        var used = new HashSet<>(reserved);
        members.forEach(member -> used.add(context.symbolProvider().toMemberName(member)));
        for (var member : members) {
            var name = context.symbolProvider().toMemberName(member);
            if (reserved.contains(name)) {
                do {
                    name += "_";
                } while (used.contains(name));
            }
            used.add(name);
            parameters.put(member, name);
        }
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
        writer.write("input = $T(", context.symbolProvider().toSymbol(input)).indent();
        parameters.forEach((member, name) -> writer.write("$L=$L,",
                context.symbolProvider().toMemberName(member),
                name));
        writer.dedent().write(")");
    }

    void writeDocs(PythonWriter writer) {
        parameters.forEach((member, name) -> {
            var docs = member.getMemberTrait(context.model(), DocumentationTrait.class)
                    .map(DocumentationTrait::getValue)
                    .orElse("The `" + context.symbolProvider().toMemberName(member) + "` input member.");
            writer.write("$L:", name).indent();
            writer.write("${L|}", writer.formatDocs(docs, context));
            writer.dedent();
        });
    }

    void writeArguments(PythonWriter writer, String inputVariable) {
        parameters.forEach((member, name) -> writer.write("$L=$L.$L,",
                name,
                inputVariable,
                context.symbolProvider().toMemberName(member)));
    }
}
