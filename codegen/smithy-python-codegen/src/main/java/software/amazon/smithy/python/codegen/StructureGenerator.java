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
import static software.amazon.smithy.python.codegen.CodegenUtils.isErrorMessage;

import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoField;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
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
import software.amazon.smithy.model.traits.TimestampFormatTrait;


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
                if (nullableIndex.isMemberNullable(member)) {
                    writer.addStdlibImport("typing", "Optional");
                    String formatString = format("$L: Optional[%s] = None,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member));
                } else if (member.hasTrait(RequiredTrait.class)) {
                    String formatString = format("$L: %s = $L,", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member),
                            getDefaultValue(writer, member));
                } else {
                    String formatString = format("$L: %s = $T($L),", getTargetFormat(member));
                    writer.write(formatString, memberName, symbolProvider.toSymbol(member),
                            CodegenUtils.getDefaultWrapperFunction(settings), getDefaultValue(writer, member));
                }
            }
        });

        writer.indent();

        writeClassDocs(isError);
        writer.write("self._has: dict[str, bool] = {}");
        if (isError) {
            writer.write("super().__init__(message)");
        }

        Stream.concat(requiredMembers.stream(), optionalMembers.stream()).forEach(member -> {
            String memberName = symbolProvider.toMemberName(member);
            if (member.hasTrait(DefaultTrait.class) && !member.hasTrait(RequiredTrait.class)) {
                writer.write("self._set_default_attr($1S, $1L)", memberName);
            } else {
                writer.write("self.$1L = $1L", memberName);
            }
        });
        writer.dedent();
        writer.write("");

        writer.write("""
                def _set_default_attr(self, name: str, value: Any) -> None:
                    if isinstance(value, $T):
                        object.__setattr__(self, name, value.value())
                        self._has[name] = False
                    else:
                        setattr(self, name, value)

                def __setattr__(self, name: str, value: Any) -> None:
                    object.__setattr__(self, name, value)
                    self._has[name] = True

                def _hasattr(self, name: str) -> bool:
                    if self._has.get(name, False):
                        return True
                    # Lists and dicts are mutable. We could make immutable variants, but
                    # that's kind of a bad experience. Instead we can just check to see if
                    # the value is empty.
                    if isinstance((v := getattr(self, name, None)), (dict, list)) and len(v) != 0:
                        self._has[name] = True
                        return True
                    return False
                """, CodegenUtils.getDefaultWrapperClass(settings));
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
        var defaultNode = member.expectTrait(DefaultTrait.class).toNode();
        var target = model.expectShape(member.getTarget());
        if (target.isTimestampShape()) {
            writer.addStdlibImport("datetime", "datetime");
            writer.addStdlibImport("datetime", "timezone");
            // We *could* let python do this parsing, but then that work has to be done every time a customer
            // runs their code.
            ZonedDateTime value = parseDefaultTimestamp(member, defaultNode);
            return String.format("datetime(%d, %d, %d, %d, %d, %d, %d, timezone.utc)", value.get(ChronoField.YEAR),
                    value.get(ChronoField.MONTH_OF_YEAR), value.get(ChronoField.DAY_OF_MONTH),
                    value.get(ChronoField.HOUR_OF_DAY), value.get(ChronoField.MINUTE_OF_HOUR),
                    value.get(ChronoField.SECOND_OF_MINUTE), value.get(ChronoField.MICRO_OF_SECOND));
        } else if (target.isBlobShape()) {
            return String.format("b'%s'", defaultNode.expectStringNode().getValue());
        }
        return switch (defaultNode.getType()) {
            case NULL -> "None";
            case BOOLEAN -> defaultNode.expectBooleanNode().getValue() ? "True" : "False";
            default -> Node.printJson(defaultNode);
        };
    }

    private ZonedDateTime parseDefaultTimestamp(MemberShape member, Node value) {
        Optional<TimestampFormatTrait> trait = member.getMemberTrait(model, TimestampFormatTrait.class);
        if (trait.isPresent()) {
            switch (trait.get().getFormat()) {
                case EPOCH_SECONDS:
                    return parseEpochTime(value);
                case DATE_TIME:
                    return parseDateTime(value);
                case HTTP_DATE:
                    return parseHttpDate(value);
                default:
                    break;
            }
        }

        if (value.isNumberNode()) {
            return parseEpochTime(value);
        } else {
            // Smithy's node validator asserts that string nodes are in the http date format if there
            // is no format explicitly given.
            return parseDateTime(value);
        }
    }

    private ZonedDateTime parseEpochTime(Node value) {
        Number number = value.expectNumberNode().getValue();
        Instant instant = Instant.ofEpochMilli(Double.valueOf(number.doubleValue() * 1000).longValue());
        return instant.atZone(ZoneId.of("UTC"));
    }

    private ZonedDateTime parseDateTime(Node value) {
        Instant instant =  Instant.from(DateTimeFormatter.ISO_INSTANT.parse(value.expectStringNode().getValue()));
        return instant.atZone(ZoneId.of("UTC"));
    }

    private ZonedDateTime parseHttpDate(Node value) {
        Instant instant = Instant.from(DateTimeFormatter.RFC_1123_DATE_TIME.parse(value.expectStringNode().getValue()));
        return instant.atZone(ZoneId.of("UTC"));
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
                    writer.openBlock("if self._hasattr($1S) and self.$1L is not None:", "", memberName, () -> {
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
}
