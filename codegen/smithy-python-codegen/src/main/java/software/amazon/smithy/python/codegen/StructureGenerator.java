/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.CodegenUtils.isErrorMessage;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.model.traits.SensitiveTrait;


/**
 * Renders structures.
 */
final class StructureGenerator implements Runnable {

    private static final Logger LOGGER = Logger.getLogger(StructureGenerator.class.getName());

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final StructureShape shape;
    private final List<MemberShape> requiredMembers;
    private final List<MemberShape> optionalMembers;
    private final Set<Shape> recursiveShapes;
    private final PythonSettings settings;

    StructureGenerator(
            Model model,
            PythonSettings settings,
            SymbolProvider symbolProvider,
            PythonWriter writer,
            StructureShape shape,
            Set<Shape>  recursiveShapes
    ) {
        this.model = model;
        this.settings = settings;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = shape;
        var required = new ArrayList<MemberShape>();
        var optional = new ArrayList<MemberShape>();
        var index = NullableIndex.of(model);
        for (MemberShape member: shape.members()) {
            if (index.isMemberNullable(member) || member.hasTrait(DefaultTrait.class)) {
                optional.add(member);
            } else {
                required.add(member);
            }
        }
        this.requiredMembers = filterMessageMembers(required);
        this.optionalMembers = filterMessageMembers(optional);
        this.recursiveShapes = recursiveShapes;
    }

    @Override
    public void run() {
        if (!shape.hasTrait(ErrorTrait.class)) {
            renderStructure();
        } else {
            renderError();
        }
    }

    /**
     * Renders a normal, non-error structure.
     */
    private void renderStructure() {
        writer.addStdlibImport("dataclasses", "dataclass");
        var symbol = symbolProvider.toSymbol(shape);


        if (shape.members().isEmpty() && !shape.hasTrait(DocumentationTrait.class)) {
            writer.write("""
                    @dataclass
                    class $L:
                        pass

                    """, symbol.getName());
            return;
        }



        writer.write("""
                @dataclass(kw_only=True)
                class $L:
                    ${C|}

                    ${C|}

                """, symbol.getName(),
                writer.consumer(w -> writeClassDocs(false)),
                writer.consumer(w -> writeProperties()));
    }

    private void renderError() {
        ErrorTrait errorTrait = shape.getTrait(ErrorTrait.class).orElseThrow(IllegalStateException::new);
        writer.addStdlibImports("typing", Set.of("Literal", "ClassVar"));
        writer.addStdlibImport("dataclasses", "dataclass");

        // TODO: Implement protocol-level customization of the error code
        var fault = errorTrait.getValue();
        var code = shape.getId().getName();
        var symbol = symbolProvider.toSymbol(shape);
        var apiError = CodegenUtils.getApiError(settings);

        writer.write("""
                @dataclass(kw_only=True)
                class $1L($2T):
                    ${5C|}

                    code: ClassVar[str] = $3S
                    fault: ClassVar[Literal["client", "server"]] = $4S

                    message: str
                    ${6C|}

                """, symbol.getName(), apiError, code, fault,
                writer.consumer(w -> writeClassDocs(true)),
                writer.consumer(w -> writeProperties()));
    }

    private void writeProperties() {
        for (MemberShape member : requiredMembers) {
            writer.pushState();
            writer.putContext("sensitive", false);
            if (member.hasTrait(SensitiveTrait.class)) {
                writer.addStdlibImport("dataclasses", "field");
                writer.putContext("sensitive", true);
            }

            var memberName = symbolProvider.toMemberName(member);
            var target = model.expectShape(member.getTarget());
            writer.putContext("quote", recursiveShapes.contains(target) ? "'" : "");
            writer.write("""
                    $L: ${quote:L}$T${quote:L}\
                    ${?sensitive} = field(repr=False)${/sensitive}
                    """,
                    memberName, symbolProvider.toSymbol(member));
            writer.popState();
        }

        for (MemberShape member : optionalMembers) {
            writer.pushState();

            var requiresField = false;
            if (member.hasTrait(SensitiveTrait.class)) {
                writer.putContext("sensitive", true);
                writer.addStdlibImport("dataclasses", "field");
                requiresField = true;
            } else {
                writer.putContext("sensitive", false);
            }

            var defaultValue = "None";
            var defaultKey = "default";
            if (member.hasTrait(DefaultTrait.class)) {
                defaultValue = getDefaultValue(writer, member);
                if (Set.of("list", "dict").contains(defaultValue)) {
                    writer.addStdlibImport("dataclasses", "field");
                    defaultKey = "default_factory";
                    requiresField = true;
                }

            } else {
                writer.putContext("nullable", true);
            }
            writer.putContext("defaultKey", defaultKey);
            writer.putContext("defaultValue", defaultValue);
            writer.putContext("useField", requiresField);

            var target = model.expectShape(member.getTarget());
            writer.putContext("quote", recursiveShapes.contains(target) ? "'" : "");

            var memberName = symbolProvider.toMemberName(member);
            writer.write("""
                    $L: ${quote:L}$T${?nullable} | None${/nullable}${quote:L} \
                    = ${^useField}${defaultValue:L}${/useField}\
                    ${?useField}\
                    field(${?sensitive}repr=False, ${/sensitive}${defaultKey:L}=${defaultValue:L})\
                    ${/useField}""", memberName, symbolProvider.toSymbol(member));

            writer.popState();
        }
    }

    private void writeClassDocs(boolean isError) {
        if (hasDocs()) {
            writer.writeDocs(() -> {
                shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.write(writer.formatDocs(trait.getValue()));
                });

                if (isError) {
                    writer.write(":param message: A message associated with the specific error.");
                }

                if (!shape.members().isEmpty()) {
                    writer.write("");
                    requiredMembers.forEach(this::writeMemberDocs);
                    optionalMembers.forEach(this::writeMemberDocs);
                }
            });
        }
    }

    private List<MemberShape> filterMessageMembers(List<MemberShape> members) {
        // Only apply this to structures that are errors.
        if (!shape.hasTrait(ErrorTrait.class)) {
            return members;
        }
        // We replace modeled message members with a static `message` member. Serialization
        // and deserialization will handle assigning them properly.
        return members.stream()
                .filter(member -> !isErrorMessage(model, member))
                .collect(Collectors.toList());
    }

    private String getDefaultValue(PythonWriter writer, MemberShape member) {
        // The default value is defined in the model is a exposed as generic
        // json, so we need to convert it to the proper type based on the target.
        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-default-trait
        var defaultNode = member.expectTrait(DefaultTrait.class).toNode();
        var target = model.expectShape(member.getTarget());
        if (target.isTimestampShape()) {
            ZonedDateTime value = CodegenUtils.parseTimestampNode(model, member, defaultNode);
            return CodegenUtils.getDatetimeConstructor(writer, value);
        } else if (target.isBlobShape()) {
            return String.format("b'%s'", defaultNode.expectStringNode().getValue());
        }
        return switch (defaultNode.getType()) {
            case NULL -> "None";
            case BOOLEAN -> defaultNode.expectBooleanNode().getValue() ? "True" : "False";
            // These will be given to a default_factory in field. They're inherently empty, so no need to
            // worry about any potential values.
            case ARRAY -> "list";
            case OBJECT -> "dict";
            default -> Node.printJson(defaultNode);
        };
    }

    private boolean hasDocs() {
        if (shape.hasTrait(DocumentationTrait.class)) {
            return true;
        }
        for (MemberShape member : shape.members()) {
            if (member.getMemberTrait(model, DocumentationTrait.class).isPresent()) {
                return true;
            }
        }
        return false;
    }

    private void writeMemberDocs(MemberShape member) {
        member.getMemberTrait(model, DocumentationTrait.class).ifPresent(trait -> {
            String memberName = symbolProvider.toMemberName(member);
            String docs = writer.formatDocs(String.format(":param %s: %s", memberName, trait.getValue()));
            writer.write(docs);
        });
    }
}
