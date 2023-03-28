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

import static java.lang.String.format;
import static software.amazon.smithy.python.codegen.CodegenUtils.isErrorMessage;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import software.amazon.smithy.codegen.core.Symbol;
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
import software.amazon.smithy.model.traits.RequiredTrait;
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
        writer.addStdlibImport("typing", "Dict");
        writer.addStdlibImport("typing", "Any");
        var symbol = symbolProvider.toSymbol(shape);
        writer.openBlock("class $L:", "", symbol.getName(), () -> {
            writeProperties(false);
            writeInit(false);
            writeAsDict(false);
            writeFromDict(false);
            writeRepr(false);
            writeEq(false);
        });
        writer.write("");
    }

    private void renderError() {
        writer.addStdlibImport("typing", "Dict");
        writer.addStdlibImport("typing", "Any");
        writer.addStdlibImport("typing", "Literal");
        // TODO: Implement protocol-level customization of the error code
        var code = shape.getId().getName();
        var symbol = symbolProvider.toSymbol(shape);
        var apiError = CodegenUtils.getApiError(settings);
        writer.openBlock("class $L($T[Literal[$S]]):", "", symbol.getName(), apiError, code, () -> {
            writer.write("code: Literal[$1S] = $1S", code);
            writer.write("message: str");
            writeProperties(true);
            writeInit(true);
            writeAsDict(true);
            writeFromDict(true);
            writeRepr(true);
            writeEq(true);
        });
        writer.write("");
    }

    private void writeProperties(boolean isError) {
        NullableIndex index = NullableIndex.of(model);
        for (MemberShape member : shape.members()) {
            if (isError && isErrorMessage(model, member)) {
                continue;
            }
            var memberName = symbolProvider.toMemberName(member);
            if (index.isMemberNullable(member)) {
                writer.addStdlibImport("typing", "Optional");
                String formatString = format("$L: Optional[%s]", getTargetFormat(member));
                writer.write(formatString, memberName, symbolProvider.toSymbol(member));
            } else {
                String formatString = format("$L: %s", getTargetFormat(member));
                writer.write(formatString, memberName, symbolProvider.toSymbol(member));
            }
        }
    }

    private void writeInit(boolean isError) {
        if (!isError && shape.members().isEmpty()) {
            writeClassDocs(false);
            return;
        }

        var nullableIndex = NullableIndex.of(model);
        writer.openBlock("def __init__(", "):", () -> {
            writer.write("self,");
            if (!shape.members().isEmpty() || isError) {
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
                if (nullableIndex.isMemberNullable(member)) {
                    writer.addStdlibImport("typing", "Optional");
                    String formatString = format("$L: Optional[%s] = None,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member));
                } else if (member.hasTrait(RequiredTrait.class)) {
                    String formatString = format("$L: %s = $L,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member),
                            getDefaultValue(writer, member));
                } else {
                    // Shapes that are simple types, lists, or maps can have default values.
                    // https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-default-trait
                    var target = model.expectShape(member.getTarget());
                    var memberSymbol = symbolProvider.toSymbol(member);
                    String formatString;
                    if (target.isDocumentShape() || target.isListShape() || target.isMapShape()) {
                        // Documents, lists, and maps can have mutable defaults so just use None in the
                        // constructor.
                        writer.addStdlibImport("typing", "Optional");
                        formatString = format("$L: Optional[%1$s] = None,", getTargetFormat(member));
                        writer.write(formatString, memberName, memberSymbol);
                    } else {
                        formatString = format("$L: %s = $L,", getTargetFormat(member));
                        writer.write(formatString, memberName, memberSymbol, getDefaultValue(writer, member));
                    }
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
            if (isOptionalDefault(member)) {
                writer.write("self.$1L = $1L if $1L is not None else $2L",
                    memberName, getDefaultValue(writer, member));
            } else {
                writer.write("self.$1L = $1L", memberName);
            }
        });
        writer.dedent();
        writer.write("");
    }

    private boolean isOptionalDefault(MemberShape member) {
        // If a member with a default value isn't required, it's optional.
        // see: https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-default-trait
        var target = model.expectShape(member.getTarget());
        return member.hasTrait(DefaultTrait.class) && !member.hasTrait(RequiredTrait.class)
            && (target.isDocumentShape() || target.isListShape() || target.isMapShape());
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

    private void writeAsDict(boolean isError) {
        writer.openBlock("def as_dict(self) -> Dict[str, Any]:", "", () -> {
            writer.writeDocs(() -> {
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
                        var targetSymbol = symbolProvider.toSymbol(target);
                        if (target.isStructureShape() || target.isUnionShape()) {
                            writer.write("$S: self.$L.as_dict(),", member.getMemberName(), memberName);
                        } else if (targetSymbol.getProperty("asDict").isPresent()) {
                            var targetAsDictSymbol = targetSymbol.expectProperty("asDict", Symbol.class);
                            writer.write("$S: $T(self.$L),", member.getMemberName(), targetAsDictSymbol, memberName);
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
                    var targetSymbol = symbolProvider.toSymbol(target);
                    writer.openBlock("if self.$1L is not None:", "", memberName, () -> {
                        if (target.isStructureShape() || target.isUnionShape()) {
                            writer.write("d[$S] = self.$L.as_dict()", member.getMemberName(), memberName);
                        } else if (targetSymbol.getProperty("asDict").isPresent()) {
                            var targetAsDictSymbol = targetSymbol.expectProperty("asDict", Symbol.class);
                            writer.write("d[$S] = $T(self.$L),", member.getMemberName(), targetAsDictSymbol,
                                    memberName);
                        } else {
                            writer.write("d[$S] = self.$L", member.getMemberName(), memberName);
                        }
                    });
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
            writer.writeDocs(() -> {
                writer.write("Creates a $L from a dictionary.\n", shapeName);
                writer.write(writer.formatDocs("""
                        The dictionary is expected to use the modeled shape names rather \
                        than the parameter names as keys to be mostly compatible with boto3."""));
            });

            if (shape.members().isEmpty() && !isError) {
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
                        Symbol targetSymbol = symbolProvider.toSymbol(target);
                        if (target.isStructureShape()) {
                            writer.write("$S: $T.from_dict(d[$S]),", memberName, targetSymbol, member.getMemberName());
                        } else if (targetSymbol.getProperty("fromDict").isPresent()) {
                            var targetFromDictSymbol = targetSymbol.expectProperty("fromDict", Symbol.class);
                            writer.write("$S: $T(d[$S]),", memberName, targetFromDictSymbol, member.getMemberName());
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
                    var targetSymbol = symbolProvider.toSymbol(target);
                    if (target.isStructureShape()) {
                        writer.write("kwargs[$S] = $T.from_dict(d[$S])", memberName, targetSymbol,
                                member.getMemberName());
                    } else if (targetSymbol.getProperty("fromDict").isPresent()) {
                        var targetFromDictSymbol = targetSymbol.expectProperty("fromDict", Symbol.class);
                        writer.write("kwargs[$S] = $T(d[$S]),", memberName, targetFromDictSymbol,
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

    private void writeRepr(boolean isError) {
        var symbol = symbolProvider.toSymbol(shape);
        writer.write("""
            def __repr__(self) -> str:
                result = "$L("
                ${C|}
                return result + ")"
            """, symbol.getName(), (Runnable) () -> writeReprMembers(isError));
    }

    private void writeReprMembers(boolean isError) {
        if (isError) {
            writer.write("result += f'message={self.message},'");
        }
        var iter = shape.members().iterator();
        while (iter.hasNext()) {
            var member = iter.next();
            var memberName = symbolProvider.toMemberName(member);
            var trailingComma = iter.hasNext() ? ", " : "";
            if (member.hasTrait(SensitiveTrait.class)) {
                // Sensitive members must not be printed
                // see: https://smithy.io/2.0/spec/documentation-traits.html#smithy-api-sensitive-trait
                writer.write("""
                    if self.$1L is not None:
                        result += f"$1L=...$2L"
                    """, memberName, trailingComma);
            } else {
                writer.write("""
                    if self.$1L is not None:
                        result += f"$1L={repr(self.$1L)}$2L"
                    """, memberName, trailingComma);
            }
        }
    }

    private void writeEq(boolean isError) {
        var symbol = symbolProvider.toSymbol(shape);
        writer.addStdlibImport("typing", "Any");
        var attributeList = new StringBuilder("[");
        if (isError) {
            attributeList.append("'message',");
        }
        for (MemberShape member : shape.members()) {
            attributeList.append(String.format("'%s',", symbolProvider.toMemberName(member)));
        }
        attributeList.append("]");

        if (!isError && shape.members().isEmpty()) {
            writer.write("""
                def __eq__(self, other: Any) -> bool:
                    return isinstance(other, $L)
                """, symbol.getName());
            return;
        }

        // Use a generator expression inside "all" here to save some space while still
        // lazily evaluating each equality check.
        writer.write("""
            def __eq__(self, other: Any) -> bool:
                if not isinstance(other, $L):
                    return False
                attributes: list[str] = $L
                return all(
                    getattr(self, a) == getattr(other, a)
                    for a in attributes
                )
            """, symbol.getName(), attributeList.toString());
    }
}
