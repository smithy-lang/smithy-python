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

                    ${C|}

                """,
                symbol.getName(),
                writer.consumer(w -> writeClassDocs()),
                writer.consumer(w -> writeProperties()),
                writer.consumer(w -> generateSerializeMethod()),
                writer.consumer(w -> generateDeserializeMethod()),
                writer.consumer(w -> generateSmithyDefaultMethod()));
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

                    ${8C|}

                """,
                symbol.getName(),
                baseError,
                fault,
                writer.consumer(w -> writeClassDocs()),
                writer.consumer(w -> writeProperties()),
                writer.consumer(w -> generateSerializeMethod()),
                writer.consumer(w -> generateDeserializeMethod()),
                writer.consumer(w -> generateSmithyDefaultMethod()));
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
        } else if (target.isEnumShape()) {
            // Wrap rather than emit a bare string so the value matches the field type.
            var enumSymbol = symbolProvider.toSymbol(target).expectProperty(SymbolProperties.ENUM_SYMBOL);
            writer.addImport(enumSymbol, enumSymbol.getName());
            return String.format("%s(\"%s\")", enumSymbol.getName(), defaultNode.expectStringNode().getValue());
        } else if (target.isIntEnumShape()) {
            var enumSymbol = symbolProvider.toSymbol(target).expectProperty(SymbolProperties.ENUM_SYMBOL);
            writer.addImport(enumSymbol, enumSymbol.getName());
            return String.format("%s(%s)", enumSymbol.getName(), defaultNode.expectNumberNode().getValue());
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
                    ${C|}
                    return kwargs

                """,
                writer.consumer(w -> deserializeMembers(shape.members())),
                schemaSymbol,
                writer.consumer(w -> writeErrorCorrection()));
        writer.popState();
    }

    /**
     * Emits client error correction for required members the server failed to serialize.
     *
     * @see <a href="https://smithy.io/2.0/spec/aggregate-types.html#client-error-correction">Smithy
     *     spec: Client error correction</a>
     */
    private void writeErrorCorrection() {
        var visitor = new MemberErrorCorrectionGenerator(context, writer);
        for (MemberShape member : requiredMembers) {
            var target = model.expectShape(member.getTarget());
            if (!MemberErrorCorrectionGenerator.hasDefault(target, model)) {
                // Streaming shapes have no synthesizable default; let the dataclass raise.
                continue;
            }
            writer.pushState();
            writer.putContext("memberName", symbolProvider.toMemberName(member));
            writer.write("""
                    if ${memberName:S} not in kwargs:
                        kwargs[${memberName:S}] = ${C|}""",
                    writer.consumer(w -> target.accept(visitor)));
            writer.popState();
        }
    }

    /**
     * Emits a {@code _smithy_default()} classmethod that constructs an instance with all
     * required members filled in via client error correction. Used to fill nested structure
     * members per the Smithy spec. Only emitted when this structure is actually referenced
     * as the target of a required structure member elsewhere in the model. If the structure
     * has any required member whose target has no synthesizable default (a streaming blob,
     * or another structure whose own required members transitively have no default),
     * {@code _smithy_default()} is also omitted.
     */
    private void generateSmithyDefaultMethod() {
        if (!isRequiredStructMemberTarget()) {
            return;
        }
        for (MemberShape member : requiredMembers) {
            var target = model.expectShape(member.getTarget());
            if (!MemberErrorCorrectionGenerator.hasDefault(target, model)) {
                return;
            }
        }
        writer.write("""
                @classmethod
                def _smithy_default(cls) -> Self:
                    return cls(${C|})
                """,
                writer.consumer(w -> writeSmithyDefaultArguments()));
    }

    /**
     * Returns true if any structure in the model has a python-required member whose target
     * is this shape.
     */
    private boolean isRequiredStructMemberTarget() {
        var index = NullableIndex.of(model);
        for (var struct : model.getStructureShapes()) {
            for (var member : struct.members()) {
                if (!index.isMemberNullable(member)
                        && !member.hasTrait(DefaultTrait.class)
                        && member.getTarget().equals(shape.getId())) {
                    return true;
                }
            }
        }
        return false;
    }

    private void writeSmithyDefaultArguments() {
        var visitor = new MemberErrorCorrectionGenerator(context, writer);
        var first = true;
        for (MemberShape member : requiredMembers) {
            var target = model.expectShape(member.getTarget());
            if (!first) {
                writer.writeInline(", ");
            }
            first = false;
            writer.writeInline("$L=", symbolProvider.toMemberName(member));
            target.accept(visitor);
        }
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
