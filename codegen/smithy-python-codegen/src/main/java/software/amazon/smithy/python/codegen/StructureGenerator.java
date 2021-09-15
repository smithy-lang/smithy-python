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

import java.util.ArrayList;
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.utils.ListUtils;


/**
 * Renders structures.
 *
 * TODO: support errors
 */
final class StructureGenerator implements Runnable {

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final StructureShape shape;
    private final List<MemberShape> requiredMembers;
    private final List<MemberShape> optionalMembers;

    StructureGenerator(Model model, SymbolProvider symbolProvider, PythonWriter writer, StructureShape shape) {
        this.model = model;
        this.symbolProvider = symbolProvider;
        this.writer = writer;
        this.shape = shape;
        List<MemberShape> required = new ArrayList<>();
        List<MemberShape> optional = new ArrayList<>();
        for (MemberShape member: shape.members()) {
            if (member.isRequired()) {
                required.add(member);
            } else {
                optional.add(member);
            }
        }
        this.requiredMembers = ListUtils.copyOf(required);
        this.optionalMembers = ListUtils.copyOf(optional);
    }

    @Override
    public void run() {
        if (!shape.hasTrait(ErrorTrait.class)) {
            renderStructure();
        }
    }

    /**
     * Renders a normal, non-error structure.
     */
    private void renderStructure() {
        writer.addStdlibImport("Dict", "Dict", "typing");
        Symbol symbol = symbolProvider.toSymbol(shape);
        writer.openBlock("class $L:", "", symbol.getName(), () -> {
            writeInit();
            writeAsDict();
            writeFromDict();
        });
        writer.write("");
    }

    private void writeInit() {
        NullableIndex nullableIndex = NullableIndex.of(model);
        writer.openBlock("def __init__(", "):", () -> {
            writer.write("self,");
            if (!shape.members().isEmpty()) {
                // Adding this star to the front prevents the use of positional arguments.
                writer.write("*,");
            }
            for (MemberShape member : requiredMembers) {
                String memberName = symbolProvider.toMemberName(member);
                writer.write("$L: $T,", memberName, symbolProvider.toSymbol(member));
            }
            for (MemberShape member : optionalMembers) {
                String memberName = symbolProvider.toMemberName(member);
                if (nullableIndex.isNullable(member)) {
                    writer.addStdlibImport("Optional", "Optional", "typing");
                    writer.write("$L: Optional[$T] = None,", memberName, symbolProvider.toSymbol(member));
                } else {
                    writer.write("$L: $T = $L,", memberName, symbolProvider.toSymbol(member), getDefaultValue(member));
                }
            }
        });

        writer.indent();
        if (hasDocs()) {
            writer.openDocComment(() -> {
                shape.getTrait(DocumentationTrait.class).ifPresent(trait -> {
                    writer.write(writer.formatDocs(trait.getValue()));
                });
                writer.write("");

                requiredMembers.forEach(this::writeMemberDocs);
                optionalMembers.forEach(this::writeMemberDocs);
            });
        }
        for (MemberShape member : shape.members()) {
            String memberName = symbolProvider.toMemberName(member);
            writer.write("self.$L = $L", memberName, memberName);
        }
        if (shape.members().isEmpty()) {
            writer.write("pass");
        }
        writer.dedent();
        writer.write("");
    }

    private String getDefaultValue(MemberShape member) {
        Shape target = model.expectShape(member.getTarget());
        switch (target.getType()) {
            case BYTE:
            case SHORT:
            case INTEGER:
            case LONG:
            case BIG_INTEGER:
            case FLOAT:
            case DOUBLE:
                return "0";
            case BIG_DECIMAL:
                return "Decimal(0)";
            case BOOLEAN:
                return "false";
            case STRING:
                return "''";
            case BLOB:
                return "b''";
            case LIST:
            case SET:
                return "[]";
            case MAP:
                return "{}";
            case TIMESTAMP:
                return "datetime(1970, 1, 1)";
            default:
                return "None";
        }
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

    private void writeAsDict() {
        writer.openBlock("def asdict(self) -> Dict:", "", () -> {
            writer.openDocComment(() -> {
                writer.write("Converts the $L to a dictionary.\n", symbolProvider.toSymbol(shape).getName());
                writer.write(writer.formatDocs("The dictionary uses the modeled shape names rather than the parameter "
                        + "names as keys to be mostly compatible with boto3."));
            });

            // If there aren't any optional members, it's best to return immediately.
            String dictPrefix = optionalMembers.isEmpty() ? "return" : "d =";
            if (requiredMembers.isEmpty()) {
                writer.write("$L {}", dictPrefix);
            } else {
                writer.openBlock("$L {", "}", dictPrefix, () -> {
                    for (MemberShape member : requiredMembers) {
                        String memberName = symbolProvider.toMemberName(member);
                        Shape target = model.expectShape(member.getTarget());
                        if (target.isStructureShape()) {
                            writer.write("$S: self.$L.asdict(),", member.getMemberName(), memberName);
                        } else {
                            writer.write("$S: self.$L,", member.getMemberName(), memberName);
                        }
                    }
                });
            }

            if (!optionalMembers.isEmpty()) {
                writer.write("");
                for (MemberShape member : optionalMembers) {
                    String memberName = symbolProvider.toMemberName(member);
                    Shape target = model.expectShape(member.getTarget());
                    // Of all the default values, only the default for timestamps isn't already falsy.
                    // So for that we need a slightly bigger check.
                    if (target.isTimestampShape()) {
                        writer.openBlock(
                                "if self.$1L is not None and self.$1L != $2L:", memberName, getDefaultValue(member));
                    } else {
                        writer.openBlock("if self.$L:", memberName);
                    }
                    if (target.isStructureShape()) {
                        writer.write("d[$S] = self.$L.asdict()", member.getMemberName(), memberName);
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

    private void writeFromDict() {
        writer.write("@staticmethod");
        String shapeName = symbolProvider.toSymbol(shape).getName();
        writer.openBlock("def fromdict(d: Dict) -> $L:", "", shapeName, () -> {
            writer.openDocComment(() -> {
                writer.write("Creates a $L from a dictionary.\n", shapeName);
                writer.write(writer.formatDocs("The dictionary is expected to use the modeled shape names rather "
                        + "than the parameter names as keys to be mostly compatible with boto3."));
            });

            if (shape.members().isEmpty()) {
                writer.write("return $L()", shapeName);
                return;
            }

            if (requiredMembers.isEmpty()) {
                writer.write("kwargs = {}");
            } else {
                writer.openBlock("kwargs = {", "}", () -> {
                    for (MemberShape member : requiredMembers) {
                        String memberName = symbolProvider.toMemberName(member);
                        writer.write("$S: d[$S],", memberName, member.getMemberName());
                    }
                });
            }
            writer.write("");

            for (MemberShape member : optionalMembers) {
                String memberName = symbolProvider.toMemberName(member);
                writer.openBlock("if $S in d:", "", member.getMemberName(), () -> {
                    writer.write("kwargs[$S] = d[$S]", memberName, member.getMemberName());
                });
            }

            writer.write("return $L(**kwargs)", shapeName);
        });
        writer.write("");
    }
}
