/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static software.amazon.smithy.python.codegen.CodegenUtils.isErrorMessage;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Collection;
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
import software.amazon.smithy.model.traits.RetryableTrait;
import software.amazon.smithy.model.traits.SensitiveTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Renders structures.
 */
@SmithyInternalApi
public final class StructureGenerator implements Runnable {

    private static final Logger LOGGER = Logger.getLogger(StructureGenerator.class.getName());

    private final Model model;
    private final SymbolProvider symbolProvider;
    private final PythonWriter writer;
    private final StructureShape shape;
    private final List<MemberShape> requiredMembers;
    private final List<MemberShape> optionalMembers;
    private final Set<Shape> recursiveShapes;
    private final PythonSettings settings;
    private final GenerationContext context;

    public StructureGenerator(
            GenerationContext context,
            PythonWriter writer,
            StructureShape shape,
            Set<Shape> recursiveShapes
    ) {
        this.context = context;
        this.model = context.model();
        this.settings = context.settings();
        this.symbolProvider = context.symbolProvider();
        this.writer = writer;
        this.shape = shape;
        var required = new ArrayList<MemberShape>();
        var optional = new ArrayList<MemberShape>();
        var index = NullableIndex.of(context.model());
        for (MemberShape member : shape.members()) {
            if (index.isMemberNullable(member) || member.hasTrait(DefaultTrait.class)) {
                optional.add(member);
            } else {
                required.add(member);
            }
        }
        this.requiredMembers = filterPropertyMembers(required);
        this.optionalMembers = filterPropertyMembers(optional);
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
        writer.write("""
                @dataclass(kw_only=True)
                class $L:
                    ${C|}

                    ${C|}

                    ${C|}

                    ${C|}

                """,
                symbol.getName(),
                writer.consumer(w -> writeClassDocs()),
                writer.consumer(w -> writeProperties()),
                writer.consumer(w -> generateSerializeMethod()),
                writer.consumer(w -> generateDeserializeMethod()));
    }

    private void renderError() {
        ErrorTrait errorTrait = shape.getTrait(ErrorTrait.class).orElseThrow(IllegalStateException::new);
        writer.addStdlibImports("typing", Set.of("Literal", "ClassVar"));
        writer.addStdlibImport("dataclasses", "dataclass");

        var fault = errorTrait.getValue();
        var symbol = symbolProvider.toSymbol(shape);
        var baseError = CodegenUtils.getServiceError(settings);
        writer.putContext("retryable", false);
        writer.putContext("throttling", false);

        var retryableTrait = shape.getTrait(RetryableTrait.class);
        if (retryableTrait.isPresent()) {
            writer.putContext("retryable", true);
            writer.putContext("throttling", retryableTrait.get().getThrottling());
        }
        writer.write("""
                @dataclass(kw_only=True)
                class $1L($2T):
                    ${4C|}

                    fault: Literal["client", "server"] | None = $3S
                    ${?retryable}
                    is_retry_safe: bool | None = True
                    ${?throttling}
                    is_throttling_error: bool = True
                    ${/throttling}
                    ${/retryable}

                    ${5C|}

                    ${6C|}

                    ${7C|}

                """,
                symbol.getName(),
                baseError,
                fault,
                writer.consumer(w -> writeClassDocs()),
                writer.consumer(w -> writeProperties()),
                writer.consumer(w -> generateSerializeMethod()),
                writer.consumer(w -> generateDeserializeMethod()));
    }

    private void writeClassDocs() {
        var docs = shape.getTrait(DocumentationTrait.class)
                .map(DocumentationTrait::getValue)
                .orElse("Dataclass for " + shape.getId().getName() + " structure.");
        writer.writeDocs(docs, context);
    }

    private void writeProperties() {
        for (MemberShape member : requiredMembers) {
            writer.pushState();
            var target = model.expectShape(member.getTarget());

            if (target.hasTrait(SensitiveTrait.class)) {
                writer.addStdlibImport("dataclasses", "field");
                writer.putContext("sensitive", true);
            } else {
                writer.putContext("sensitive", false);
            }

            var memberName = symbolProvider.toMemberName(member);
            writer.putContext("quote", recursiveShapes.contains(target) ? "'" : "");
            writer.write("""
                    $L: ${quote:L}$T${quote:L}\
                    ${?sensitive} = field(repr=False)${/sensitive}
                    $C
                    """,
                    memberName,
                    symbolProvider.toSymbol(member),
                    writer.consumer(w -> writeMemberDocs(member)));
            writer.popState();
        }

        for (MemberShape member : optionalMembers) {
            writer.pushState();
            var target = model.expectShape(member.getTarget());

            var requiresField = false;
            if (target.hasTrait(SensitiveTrait.class)) {
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
                if (target.isDocumentShape() || defaultValue.startsWith("list[") || defaultValue.startsWith("dict[")) {
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

            writer.putContext("quote", recursiveShapes.contains(target) ? "'" : "");

            var memberName = symbolProvider.toMemberName(member);
            writer.write("""
                    $L: ${quote:L}$T${?nullable} | None${/nullable}${quote:L} \
                    = ${^useField}${defaultValue:L}${/useField}\
                    ${?useField}\
                    field(${?sensitive}repr=False, ${/sensitive}${defaultKey:L}=${defaultValue:L})\
                    ${/useField}
                    $C
                    """,
                    memberName,
                    symbolProvider.toSymbol(member),
                    writer.consumer(w -> writeMemberDocs(member)));
            writer.popState();
        }
    }

    private void writeMemberDocs(MemberShape member) {
        member.getMemberTrait(model, DocumentationTrait.class).ifPresent(trait -> {
            writer.writeDocs(trait.getValue(), context);
        });
    }

    private List<MemberShape> filterPropertyMembers(List<MemberShape> members) {
        if (!shape.hasTrait(ErrorTrait.class)) {
            return members.stream().filter(this::filterEventStreamMember).toList();
        }
        // We replace modeled message members with a static `message` member. Serialization
        // and deserialization will handle assigning them properly.
        return members.stream()
                .filter(member -> !isErrorMessage(model, member))
                .filter(this::filterEventStreamMember)
                .collect(Collectors.toList());
    }

    private boolean filterEventStreamMember(MemberShape member) {
        var target = model.expectShape(member.getTarget());
        return !(target.isUnionShape() && target.hasTrait(StreamingTrait.class));
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

        if (target.isDocumentShape()) {
            return String.format("lambda: Document(%s)", switch (defaultNode.getType()) {
                case NULL -> "None";
                case BOOLEAN -> defaultNode.expectBooleanNode().getValue() ? "True" : "False";
                case ARRAY -> "list()";
                case OBJECT -> "dict()";
                default -> Node.printJson(defaultNode);
            });
        }

        return switch (defaultNode.getType()) {
            case NULL -> "None";
            case BOOLEAN -> defaultNode.expectBooleanNode().getValue() ? "True" : "False";
            // These will be given to a default_factory in field. They're inherently empty, so no need to
            // worry about any potential values.
            case ARRAY, OBJECT -> symbolProvider.toSymbol(target).getName();
            default -> Node.printJson(defaultNode);
        };
    }

    private void generateSerializeMethod() {
        writer.pushState();
        writer.addImport("smithy_core.serializers", "ShapeSerializer");

        writer.putContext("schema", symbolProvider.toSymbol(shape).expectProperty(SymbolProperties.SCHEMA));
        writer.write("""
                def serialize(self, serializer: ShapeSerializer):
                    serializer.write_struct(${schema:T}, self)

                """);

        var serializeableMembers = filterMembers();
        writer.write("def serialize_members(self, serializer: ShapeSerializer):").indent();
        if (serializeableMembers.isEmpty()) {
            writer.write("pass");
        } else {
            for (MemberShape member : serializeableMembers) {
                writer.pushState();
                var target = model.expectShape(member.getTarget());
                writer.putContext("propertyName", symbolProvider.toMemberName(member));
                if (isNullable(member)) {
                    var gen = new MemberSerializerGenerator(context, writer, member, "serializer");
                    writer.write("""
                            if self.${propertyName:L} is not None:
                                ${C|}
                            """,
                            writer.consumer(w -> target.accept(gen)));
                } else {
                    target.accept(new MemberSerializerGenerator(context, writer, member, "serializer"));
                }
                writer.popState();
            }
        }
        writer.dedent().popState();
    }

    private List<MemberShape> filterMembers() {
        return shape.members()
                .stream()
                .filter(member -> {
                    var target = model.expectShape(member.getTarget());
                    return !(target.hasTrait(StreamingTrait.class) && target.isUnionShape());
                })
                .toList();
    }

    private boolean isNullable(MemberShape member) {
        if (!NullableIndex.of(model).isMemberNullable(member)) {
            return false;
        }
        var target = model.expectShape(member.getTarget());
        return !target.isDocumentShape() || member.getMemberTrait(model, DefaultTrait.class).isEmpty();
    }

    private void generateDeserializeMethod() {
        writer.pushState();
        writer.addLogger();
        writer.addStdlibImports("typing", Set.of("Self", "Any"));
        writer.addImport("smithy_core.deserializers", "ShapeDeserializer");
        writer.addImport("smithy_core.schemas", "Schema");

        var schemaSymbol = symbolProvider.toSymbol(shape).expectProperty(SymbolProperties.SCHEMA);
        writer.putContext("schema", schemaSymbol);

        // TODO: either formalize deserialize_kwargs or remove it when http serde is converted
        writer.write("""
                @classmethod
                def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
                    return cls(**cls.deserialize_kwargs(deserializer))

                @classmethod
                def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:
                    kwargs: dict[str, Any] = {}

                    def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
                        match schema.expect_member_index():
                            ${C|}
                            case _:
                                logger.debug("Unexpected member schema: %s", schema)

                    deserializer.read_struct($T, consumer=_consumer)
                    return kwargs

                """,
                writer.consumer(w -> deserializeMembers(shape.members())),
                schemaSymbol);
        writer.popState();
    }

    private void deserializeMembers(Collection<MemberShape> members) {
        int index = -1;
        for (MemberShape member : members) {
            index++;
            var target = model.expectShape(member.getTarget());
            if (target.hasTrait(StreamingTrait.class) && target.isUnionShape()) {
                continue;
            }
            writer.write("""
                    case $L:
                        kwargs[$S] = ${C|}
                    """,
                    index,
                    symbolProvider.toMemberName(member),
                    writer.consumer(
                            w -> target.accept(new MemberDeserializerGenerator(context, writer, member, "de"))));
        }
    }
}
