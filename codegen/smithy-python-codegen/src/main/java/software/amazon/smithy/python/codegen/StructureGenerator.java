/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import static java.lang.String.format;
import static software.amazon.smithy.python.codegen.CodegenUtils.DEFAULT_TIMESTAMP;
import static software.amazon.smithy.python.codegen.CodegenUtils.isErrorMessage;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.ErrorTrait;


/**
 * Renders structures.
 */
final class StructureGenerator implements Runnable {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final StructureShape shape;
    private final List<MemberShape> requiredMembers;
    private final List<MemberShape> optionalMembers;
    private final Set<Shape> recursiveShapes;

    StructureGenerator(
            Model model,
            SymbolProvider symbolProvider,
            PythonWriter writer,
            StructureShape shape,
            Set<Shape>  recursiveShapes
    ) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = shape;
        var required = new ArrayList<MemberShape>();
        var optional = new ArrayList<MemberShape>();
        for (MemberShape member: shape.members()) {
            if (member.isRequired()) {
                required.add(member);
            } else {
                optional.add(member);
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
        writer.addStdlibImport("Dict", "Dict", "typing");
        writer.addStdlibImport("Any", "Any", "typing");
        var symbol = symbolProvider.toSymbol(shape);
        writer.openBlock("class $L:", "", symbol.getName(), () -> {
            writeInit(false);
            writeAsDict(false);
            writeFromDict(false);
        });
        writer.write("");
    }

    private void renderError() {
        writer.addStdlibImport("Dict", "Dict", "typing");
        writer.addStdlibImport("Any", "Any", "typing");
        writer.addStdlibImport("Literal", "Literal", "typing");
        // TODO: Implement protocol-level customization of the error code
        var code = shape.getId().getName();
        var symbol = symbolProvider.toSymbol(shape);
        writer.openBlock("class $L($T[Literal[$S]]):", "", symbol.getName(), CodegenUtils.API_ERROR, code, () -> {
            writer.write("code: Literal[$1S] = $1S", code);
            writeInit(true);
            writeAsDict(true);
            writeFromDict(true);
        });
        writer.write("");
    }

    private void writeInit(boolean isError) {
        if (!isError && shape.members().isEmpty()) {
            writeClassDocs(false);
            return;
        }

        var nullableIndex = NullableIndex.of(model);
        writer.openBlock("def __init__(", "):", () -> {
            writer.write("self,");
            if (!shape.members().isEmpty()) {
                // Adding this star to the front prevents the use of positional arguments.
                writer.write("*,");
            }
            if (isError) {
                writer.write("message: str,");
            }
            for (MemberShape member : requiredMembers) {
                var memberName = symbolProvider.toMemberName(member);
                String formatString = format("$L: %s,", getTargetFormat(member));
                writer.write(formatString, memberName, symbolProvider.toSymbol(member));
            }
            for (MemberShape member : optionalMembers) {
                var memberName = symbolProvider.toMemberName(member);
                if (nullableIndex.isNullable(member)) {
                    writer.addStdlibImport("Optional", "Optional", "typing");
                    String formatString = format("$L: Optional[%s] = None,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member));
                } else {
                    String formatString = format("$L: %s = $L,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member), getDefaultValue(member));
                }
            }
        });

        writer.indent();

        writeClassDocs(isError);
        if (isError) {
            writer.write("super().__init__(message)");
        }
        Stream.concat(requiredMembers.stream(), optionalMembers.stream()).forEach(member -> {
            String memberName = symbolProvider.toMemberName(member);
            writer.write("self.$L = $L", memberName, memberName);
        });
        if (shape.members().isEmpty() && !isError) {
            writer.write("pass");
        }
        writer.dedent();
        writer.write("");
    }

    private void writeClassDocs(boolean isError) {
        if (hasDocs()) {
            writer.openDocComment(() -> {
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
        if (!shape.hasTrait(ErrorTrait.class)) {
            return members;
        }
        // We replace modeled message members with a static `message` member. Serialization
        // and deserialization will handle assigning them properly.
        return members.stream()
                .filter(member -> !isErrorMessage(model, member))
                .collect(Collectors.toList());
    }

    private String getTargetFormat(MemberShape member) {
        Shape target = model.expectShape(member.getTarget());
        // Recursive shapes may be referenced before they're defined even with
        // a topological sort. So forward references need to be used when
        // referencing them.
        if (recursiveShapes.contains(target)) {
            return "'$T'";
        }
        return "$T";
    }

    private String getDefaultValue(MemberShape member) {
        Shape target = model.expectShape(member.getTarget());
        return switch (target.getType()) {
            case BYTE, SHORT, INTEGER, LONG, BIG_INTEGER, FLOAT, DOUBLE -> "0";
            case BIG_DECIMAL -> "Decimal(0)";
            case BOOLEAN -> "False";
            case STRING -> "''";
            case BLOB -> "b''";
            case LIST, SET -> "[]";
            case MAP -> "{}";
            case TIMESTAMP -> {
                writer.addUseImports(DEFAULT_TIMESTAMP);
                yield DEFAULT_TIMESTAMP.getName();
            }
            default -> "None";
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

    private void writeAsDict(boolean isError) {
        writer.openBlock("def as_dict(self) -> Dict[str, Any]:", "", () -> {
            writer.openDocComment(() -> {
                writer.write("Converts the $L to a dictionary.\n", symbolProvider.toSymbol(shape).getName());
                writer.write(writer.formatDocs("""
                        The dictionary uses the modeled shape names rather than the parameter names \
                        as keys to be mostly compatible with boto3."""));
            });

            // If there aren't any optional members, it's best to return immediately.
            String dictPrefix = optionalMembers.isEmpty() ? "return" : "d: Dict[str, Any] =";
            if (requiredMembers.isEmpty() && !isError) {
                writer.write("$L {}", dictPrefix);
            } else {
                writer.openBlock("$L {", "}", dictPrefix, () -> {
                    if (isError) {
                        writer.write("'message': self.message,");
                        writer.write("'code': self.code,");
                    }
                    for (MemberShape member : requiredMembers) {
                        var memberName = symbolProvider.toMemberName(member);
                        var target = model.expectShape(member.getTarget());
                        if (target.isStructureShape()) {
                            writer.write("$S: self.$L.as_dict(),", member.getMemberName(), memberName);
                        } else {
                            writer.write("$S: self.$L,", member.getMemberName(), memberName);
                        }
                    }
                });
            }

            if (!optionalMembers.isEmpty()) {
                writer.write("");
                for (MemberShape member : optionalMembers) {
                    var memberName = symbolProvider.toMemberName(member);
                    var target = model.expectShape(member.getTarget());
                    // Of all the default values, only the default for timestamps isn't already falsy.
                    // So for that we need a slightly bigger check.
                    if (target.isTimestampShape()) {
                        writer.openBlock(
                                "if self.$1L is not None and self.$1L != $2L:", memberName, getDefaultValue(member));
                    } else {
                        writer.openBlock("if self.$L:", memberName);
                    }
                    if (target.isStructureShape()) {
                        writer.write("d[$S] = self.$L.as_dict()", member.getMemberName(), memberName);
                    } else {
                        writer.write("d[$S] = self.$L", member.getMemberName(), memberName);
                    }
                    writer.closeBlock("");
                }
                writer.write("return d");
            }
        });
        writer.write("");
    }

    private void writeFromDict(boolean isError) {
        writer.write("@staticmethod");
        var shapeName = symbolProvider.toSymbol(shape).getName();
        writer.openBlock("def from_dict(d: Dict[str, Any]) -> $S:", "", shapeName, () -> {
            writer.openDocComment(() -> {
                writer.write("Creates a $L from a dictionary.\n", shapeName);
                writer.write(writer.formatDocs("""
                        The dictionary is expected to use the modeled shape names rather \
                        than the parameter names as keys to be mostly compatible with boto3."""));
            });

            if (shape.members().isEmpty()) {
                writer.write("return $L()", shapeName);
                return;
            }

            if (requiredMembers.isEmpty() && !isError) {
                writer.write("kwargs: Dict[str, Any] = {}");
            } else {
                writer.openBlock("kwargs: Dict[str, Any] = {", "}", () -> {
                    if (isError) {
                        writer.write("'message': d['message'],");
                    }
                    for (MemberShape member : requiredMembers) {
                        var memberName = symbolProvider.toMemberName(member);
                        var target = model.expectShape(member.getTarget());
                        if (target.isStructureShape()) {
                            Symbol targetSymbol = symbolProvider.toSymbol(target);
                            writer.write("$S: $T.from_dict(d[$S]),", memberName, targetSymbol, member.getMemberName());
                        } else {
                            writer.write("$S: d[$S],", memberName, member.getMemberName());
                        }
                    }
                });
            }
            writer.write("");

            for (MemberShape member : optionalMembers) {
                var memberName = symbolProvider.toMemberName(member);
                var target = model.expectShape(member.getTarget());
                writer.openBlock("if $S in d:", "", member.getMemberName(), () -> {
                    if (target.isStructureShape()) {
                        var targetSymbol = symbolProvider.toSymbol(target);
                        writer.write("kwargs[$S] = $T.from_dict(d[$S])", memberName, targetSymbol,
                                member.getMemberName());
                    } else {
                        writer.write("kwargs[$S] = d[$S]", memberName, member.getMemberName());
                    }
                });
            }

            writer.write("return $L(**kwargs)", shapeName);
        });
        writer.write("");
    }
}
