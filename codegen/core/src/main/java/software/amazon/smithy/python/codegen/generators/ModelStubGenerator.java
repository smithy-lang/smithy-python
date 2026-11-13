/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.UnaryOperator;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.knowledge.OperationIndex;
import software.amazon.smithy.model.shapes.EnumShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.shapes.UnionShape;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.EnumValueTrait;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.InputParams;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Emits {@code models.pyi}: the typed surface for static tooling. The runtime
 * {@code models.py} builds these classes on demand; the stub declares them (and the
 * operation constants, with concrete {@code APIOperation[Input, Output]} type args) so
 * pyright and IDEs see the full types without importing the lazy runtime.
 */
@SmithyInternalApi
public final class ModelStubGenerator implements Runnable {

    private static final int STUB_PARTITION_SIZE = 250;
    private static final Symbol TYPED_DICT = typingSymbol("TypedDict");
    private static final Symbol REQUIRED = typingSymbol("Required");
    // Models type a streaming body as the async client's StreamingBlob, which is a
    // superset of this one of the same name, so this one is imported under an alias.
    private static final Symbol SYNC_STREAMING_BLOB = Symbol.builder()
            .name("StreamingBlob")
            .namespace("smithy_core.interfaces", ".")
            .build();
    private static final String SYNC_STREAMING_BLOB_ALIAS = "SyncStreamingBlob";

    private final GenerationContext context;
    private final PythonSettings settings;
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final List<Shape> shapes;
    private final InputParams inputParams;

    public ModelStubGenerator(GenerationContext context, List<Shape> shapes) {
        this.context = context;
        this.settings = context.settings();
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.shapes = shapes;
        this.inputParams = new InputParams(context);
    }

    @Override
    public void run() {
        var module = settings.moduleName();
        var filename = String.format("src/%s/models.pyi", module);
        var namespace = String.format("%s.models", module);
        var modelShapes = shapes.stream()
                .filter(this::isModelShape)
                .toList();

        if (modelShapes.size() <= STUB_PARTITION_SIZE) {
            context.writerDelegator().useFileWriter(filename, namespace, writer -> {
                writePreamble(writer);
                writeShapes(writer, modelShapes, UnaryOperator.identity());
                writeOperations(writer);
            });
            return;
        }

        var partitions = new ArrayList<List<Shape>>();
        for (int start = 0; start < modelShapes.size(); start += STUB_PARTITION_SIZE) {
            partitions.add(modelShapes.subList(start, Math.min(start + STUB_PARTITION_SIZE, modelShapes.size())));
        }
        context.writerDelegator().useFileWriter(filename, namespace, writer -> {
            for (int i = 0; i < partitions.size(); i++) {
                var partition = partitions.get(i);
                writer.openBlock(
                        String.format("from ._private.models_%d import (", i),
                        ")",
                        () -> {
                            for (var shape : partition) {
                                for (var name : stubNames(shape)) {
                                    writer.write("$L as $L,", name, name);
                                }
                            }
                        });
                writer.write("");
            }
            writePreamble(writer);
            writeOperations(writer);
        });

        for (int i = 0; i < partitions.size(); i++) {
            var partitionFilename = String.format("src/%s/_private/models_%d.pyi", module, i);
            var partitionNamespace = String.format("%s._private.models_%d", module, i);
            var partition = partitions.get(i);
            context.writerDelegator().useFileWriter(partitionFilename, partitionNamespace, writer -> {
                writer.addImport(module + ".models", "_SerdeShape");
                if (partition.stream().anyMatch(shape -> shape.hasTrait(ErrorTrait.class))) {
                    writer.addImport(module + ".models", "ServiceError");
                }
                var localNames = partition.stream()
                        .flatMap(shape -> stubNames(shape).stream())
                        .collect(java.util.stream.Collectors.toUnmodifiableSet());
                writeShapes(
                        writer,
                        partition,
                        symbol -> localizeSymbol(symbol, partitionNamespace, localNames));
            });
        }
    }

    private void writePreamble(PythonWriter writer) {
        writer.addStdlibImport("typing", "Self");
        writer.addImport("smithy_core.exceptions", "ModeledError");
        writer.addImport("smithy_core.serializers", "ShapeSerializer");
        writer.addImport("smithy_core.deserializers", "ShapeDeserializer");

        // Concrete serde base: the runtime attaches these methods to every built
        // model class, so declaring them here (implemented, not abstract) lets the
        // classes satisfy SerializeableStruct/DeserializeableShape without listing
        // the methods per class or appearing abstract to the type checker.
        writer.write("""
                class _SerdeShape:
                    def serialize(self, serializer: ShapeSerializer) -> None: ...
                    def serialize_members(self, serializer: ShapeSerializer) -> None: ...
                    @classmethod
                    def deserialize(cls, deserializer: ShapeDeserializer) -> Self: ...

                class ServiceError(ModeledError):
                    \"""
                    Base error for all errors in the service.

                    Some exceptions do not extend from this class, including
                    synthetic, implicit, and shared exception types.
                    \"""
                """);
    }

    private void writeShapes(
            PythonWriter writer,
            List<Shape> modelShapes,
            UnaryOperator<Symbol> typeResolver
    ) {
        for (var shape : modelShapes) {
            switch (shape.getType()) {
                case STRUCTURE -> writeStruct(writer, shape.asStructureShape().get(), typeResolver);
                case UNION -> writeUnion(writer, shape.asUnionShape().get(), typeResolver);
                case ENUM -> writeEnum(writer, shape.asEnumShape().get());
                case INT_ENUM -> writeIntEnum(writer, shape.asIntEnumShape().get());
                default -> {
                }
            }
        }
    }

    private void writeOperations(PythonWriter writer) {
        for (var shape : shapes) {
            if (shape.isOperationShape()) {
                writeOperation(writer, shape.asOperationShape().get());
            }
        }
    }

    // Every name a shape declares in the stub. The public stub re-exports each of them
    // from the shape's partition, and a reference to one from inside that partition is
    // local. A shape's dictionary forms are declared beside its model, so they are
    // among its names: left out, they would exist only in the private partition.
    private List<String> stubNames(Shape shape) {
        if (shape.isUnionShape()) {
            var symbol = symbolProvider.toSymbol(shape);
            var names = new ArrayList<String>();
            for (var member : shape.asUnionShape().get().members()) {
                names.add(symbolProvider.toSymbol(member).getName());
            }
            names.add(symbol.expectProperty(SymbolProperties.UNION_UNKNOWN).getName());
            names.add(symbol.getName());
            names.add(symbol.expectProperty(SymbolProperties.DESERIALIZER).getName());
            if (inputParams.hasParams(shape)) {
                for (var member : shape.asUnionShape().get().members()) {
                    names.add(inputParams.paramsSymbol(member).getName());
                }
                names.add(inputParams.paramsSymbol(shape).getName());
            }
            return names;
        }
        if (shape.isEnumShape() || shape.isIntEnumShape()) {
            return List.of(symbolProvider.toSymbol(shape)
                    .expectProperty(SymbolProperties.ENUM_SYMBOL)
                    .getName());
        }
        var names = new ArrayList<String>();
        names.add(symbolProvider.toSymbol(shape).getName());
        if (inputParams.hasParams(shape)) {
            names.add(inputParams.paramsSymbol(shape).getName());
            if (inputParams.hasAsyncParams(shape)) {
                names.add(inputParams.asyncParamsSymbol(shape).getName());
            }
        }
        return names;
    }

    private boolean isModelShape(Shape shape) {
        return switch (shape.getType()) {
            case STRUCTURE, UNION, ENUM, INT_ENUM -> true;
            default -> false;
        };
    }

    private void writeStruct(
            PythonWriter writer,
            StructureShape shape,
            UnaryOperator<Symbol> typeResolver
    ) {
        writer.addStdlibImport("dataclasses", "dataclass");
        var symbol = symbolProvider.toSymbol(shape);
        var name = symbol.getName();
        writer.addLocallyDefinedSymbol(symbol);
        var isError = shape.hasTrait(ErrorTrait.class);
        var base = isError
                ? "(ServiceError, _SerdeShape)"
                : "(_SerdeShape)";
        var index = NullableIndex.of(model);
        writer.openBlock("@dataclass(kw_only=True)\nclass $L$L:", "", name, base, () -> {
            writeShapeDocs(writer, shape, "Dataclass for " + shape.getId().getName() + " structure.");
            var members = shape.members()
                    .stream()
                    .filter(m -> !CodegenUtils.isErrorMessage(model, m))
                    .filter(m -> !CodegenUtils.isEventStreamMember(model, m))
                    .toList();
            if (members.isEmpty() && !carriesResponseMetadata(shape)) {
                return;
            }
            for (var member : members) {
                var memberName = symbolProvider.toMemberName(member);
                var mandatory = CodegenUtils.isRequiredMember(index, member)
                        && !OperationIndex.of(model).isInputStructure(shape);
                if (mandatory) {
                    writer.write("$L: $T", memberName, typeResolver.apply(memberTypeSymbol(member)));
                } else if (hasNonNullDefault(member)) {
                    writer.write("$L: $T = ...", memberName, typeResolver.apply(memberTypeSymbol(member)));
                } else {
                    writer.write("$L: $T | None = ...", memberName, typeResolver.apply(memberTypeSymbol(member)));
                }
                writeMemberDocs(writer, member);
            }
            if (carriesResponseMetadata(shape)) {
                writer.write("response_metadata: $T = ...", RuntimeTypes.RESPONSE_METADATA);
                writer.writeDocs("""
                        Metadata about the response that produced this output.

                        Use this to recover the request identifiers a service's support team \
                        needs in order to investigate a call. Members of the metadata are \
                        individually optional.""", context);
            }
        });
        writer.write("");
        if (inputParams.hasParams(shape)) {
            writeStructParams(writer, shape, name, typeResolver);
        }
    }

    // The dictionary a caller may pass in place of the model. It exists only here:
    // at runtime the name resolves to plain `dict`, so importing it builds nothing.
    // Each key is documented as the model's field is: an editor shows a key's
    // documentation from the dictionary form being written, not from the model. The
    // class itself only says what it is the dictionary form of.
    //
    // It is declared right after its model, so in a partitioned stub the two share a
    // partition and the public stub re-exports both (see stubNames).
    //
    // The two clients accept different streaming bodies, so an input with one has
    // two forms. The plain form takes what the sync client accepts, which the async
    // client accepts too. The async form also takes async streams.
    private void writeStructParams(
            PythonWriter writer,
            StructureShape shape,
            String modelName,
            UnaryOperator<Symbol> typeResolver
    ) {
        var paramsSymbol = inputParams.paramsSymbol(shape);
        if (!inputParams.hasAsyncParams(shape)) {
            writeStructParams(writer,
                    shape,
                    paramsSymbol,
                    false,
                    String.format("Dictionary form of `%s`.", modelName),
                    typeResolver);
            return;
        }
        var asyncSymbol = inputParams.asyncParamsSymbol(shape);
        writer.addImport(SYNC_STREAMING_BLOB.getNamespace(), SYNC_STREAMING_BLOB.getName(), SYNC_STREAMING_BLOB_ALIAS);
        writeStructParams(writer,
                shape,
                paramsSymbol,
                true,
                "Dictionary form of `" + modelName + "` that either client accepts.\n\n"
                        + "Its streaming body is one a sync client can send. Use `" + asyncSymbol.getName()
                        + "` for an async stream.",
                typeResolver);
        writeStructParams(writer,
                shape,
                asyncSymbol,
                false,
                "Dictionary form of `" + modelName + "` for the async client.\n\n"
                        + "Its streaming body may also be an async stream.",
                typeResolver);
    }

    private void writeStructParams(
            PythonWriter writer,
            StructureShape shape,
            Symbol paramsSymbol,
            boolean syncBody,
            String docs,
            UnaryOperator<Symbol> typeResolver
    ) {
        writer.addLocallyDefinedSymbol(paramsSymbol);
        writer.openBlock("class $L($T, total=False):", "", paramsSymbol.getName(), TYPED_DICT, () -> {
            if (docs.contains("\n")) {
                writer.writeDocs(docs, context);
            } else {
                writer.write("\"\"\"$L\"\"\"", docs);
            }
            for (var member : shape.members()) {
                if (CodegenUtils.isErrorMessage(model, member) || !inputParams.isParameter(member)) {
                    continue;
                }
                var memberName = symbolProvider.toMemberName(member);
                var type = syncBody && inputParams.isStreamingBlob(member)
                        ? SYNC_STREAMING_BLOB_ALIAS
                        : paramType(writer, member, typeResolver);
                if (inputParams.mustBeSet(member)) {
                    writer.write("$L: $T[$L]", memberName, REQUIRED, type);
                } else {
                    writer.write("$L: $L | None", memberName, type);
                }
                writeMemberDocs(writer, member);
            }
        });
        writer.write("");
    }

    // A union's dictionary form sets exactly one variant, so it is the union of one
    // single-key dictionary per variant: a type checker then rejects a dictionary
    // that sets none or more than one. Each key carries its variant's documentation.
    private void writeUnionParams(PythonWriter writer, UnionShape shape, UnaryOperator<Symbol> typeResolver) {
        var variantNames = new ArrayList<String>();
        for (var member : shape.members()) {
            var variantSymbol = inputParams.paramsSymbol(member);
            writer.addLocallyDefinedSymbol(variantSymbol);
            variantNames.add(variantSymbol.getName());
            writer.openBlock("class $L($T):", "", variantSymbol.getName(), TYPED_DICT, () -> {
                writer.write("$L: $L",
                        symbolProvider.toMemberName(member),
                        paramType(writer, member, typeResolver));
                writeMemberDocs(writer, member);
            });
            writer.write("");
        }
        var paramsSymbol = inputParams.paramsSymbol(shape);
        writer.addLocallyDefinedSymbol(paramsSymbol);
        writer.write("$L = Union[$L]", paramsSymbol.getName(), String.join(" | ", variantNames));
        writer.writeDocs(
                String.format("Dictionary form of `%s`, setting exactly one variant.",
                        symbolProvider.toSymbol(shape).getName()),
                context);
        writer.write("");
    }

    // Spells the type a dictionary form accepts for a member. Every symbol in it, a
    // model's and a dictionary form's alike, goes through the resolver, so that in a
    // partitioned stub one declared in the same partition is referred to locally and
    // any other is imported from the public models module, which re-exports it.
    private String paramType(PythonWriter writer, MemberShape member, UnaryOperator<Symbol> typeResolver) {
        return inputParams.typeOf(member, symbol -> writer.format("$T", typeResolver.apply(symbol)));
    }

    // Must agree with StructureGenerator: a defaulted member is never None at runtime,
    // except a non-document `@default: null`; a document default is a Document(None).
    private boolean hasNonNullDefault(MemberShape member) {
        var defaultTrait = member.getTrait(DefaultTrait.class);
        if (defaultTrait.isEmpty()) {
            return false;
        }
        return model.expectShape(member.getTarget()).isDocumentShape()
                || !defaultTrait.get().toNode().isNullNode();
    }

    // The runtime attaches the DocumentationTrait text at build time; the stub is the
    // only surface IDEs/pyright read, so docstrings must be emitted here too.
    private void writeShapeDocs(PythonWriter writer, Shape shape, String fallback) {
        var docs = shape.getTrait(DocumentationTrait.class)
                .map(DocumentationTrait::getValue)
                .orElse(fallback);
        writer.writeDocs(docs, context);
    }

    private void writeMemberDocs(PythonWriter writer, MemberShape member) {
        CodegenUtils.getMemberDocs(model, member).ifPresent(docs -> writer.writeDocs(docs, context));
    }

    private boolean carriesResponseMetadata(Shape shape) {
        return shape.hasTrait(ErrorTrait.class) || OperationIndex.of(model).isOutputStructure(shape);
    }

    private void writeUnion(
            PythonWriter writer,
            UnionShape shape,
            UnaryOperator<Symbol> typeResolver
    ) {
        writer.addStdlibImport("dataclasses", "dataclass");
        writer.addStdlibImport("typing", "Union");
        writer.addImport("smithy_core.deserializers", "ShapeDeserializer");
        var parentSymbol = symbolProvider.toSymbol(shape);
        var parentName = parentSymbol.getName();
        writer.addLocallyDefinedSymbol(parentSymbol);
        var variantNames = new ArrayList<String>();
        for (var member : shape.members()) {
            var variantSymbol = symbolProvider.toSymbol(member);
            var variantName = variantSymbol.getName();
            writer.addLocallyDefinedSymbol(variantSymbol);
            variantNames.add(variantName);
            var target = model.expectShape(member.getTarget());
            writer.openBlock(
                    "@dataclass\nclass $L(_SerdeShape):",
                    "",
                    variantName,
                    () -> {
                        writeMemberDocs(writer, member);
                        writer.write("value: $T", typeResolver.apply(valueTypeSymbol(target)));
                    });
            writer.write("");
        }
        var unknownSymbol = parentSymbol.expectProperty(SymbolProperties.UNION_UNKNOWN);
        var unknownName = unknownSymbol.getName();
        writer.addLocallyDefinedSymbol(unknownSymbol);
        writer.openBlock(
                "@dataclass\nclass $L(_SerdeShape):",
                "",
                unknownName,
                () -> {
                    writer.writeDocs("""
                            Represents an unknown variant.

                            If you receive this value, you will need to update your library to receive the \
                            parsed value.

                            This value may not be deliberately sent.""", context);
                    writer.write("tag: str");
                });
        writer.write("");
        variantNames.add(unknownName);
        writer.write("$L = Union[$L]", parentName, String.join(" | ", variantNames));
        shape.getTrait(DocumentationTrait.class)
                .ifPresent(trait -> writer.writeDocs(trait.getValue(), context));
        writer.write("");
        // The runtime builds a `_<Union>Deserializer().deserialize(d)` helper for event-
        // stream unions; declare it so client.py's event-stream wiring type-checks.
        var deserializerSymbol = parentSymbol.expectProperty(SymbolProperties.DESERIALIZER);
        var deserializerName = deserializerSymbol.getName();
        writer.addLocallyDefinedSymbol(deserializerSymbol);
        writer.openBlock(
                "class $L:",
                "",
                deserializerName,
                () -> writer.write(
                        "def deserialize(self, deserializer: ShapeDeserializer) -> $L: ...",
                        parentName));
        writer.write("");
        if (inputParams.hasParams(shape)) {
            writeUnionParams(writer, shape, typeResolver);
        }
    }

    private static Symbol typingSymbol(String name) {
        return Symbol.builder()
                .name(name)
                .namespace("typing", ".")
                .putProperty(SymbolProperties.STDLIB, true)
                .build();
    }

    private software.amazon.smithy.codegen.core.Symbol valueTypeSymbol(Shape target) {
        // Enum members are typed as their base str/int (the symbol the provider gives a
        // enum/int-enum shape), matching the eager generator: the field accepts the raw
        // backing value, and the enum class is only a convenience for callers.
        return symbolProvider.toSymbol(target);
    }

    private software.amazon.smithy.codegen.core.Symbol memberTypeSymbol(MemberShape member) {
        return symbolProvider.toSymbol(member);
    }

    private Symbol localizeSymbol(
            Symbol symbol,
            String partitionNamespace,
            Set<String> localNames
    ) {
        var references = symbol.getReferences()
                .stream()
                .map(reference -> reference.toBuilder()
                        .symbol(localizeSymbol(reference.getSymbol(), partitionNamespace, localNames))
                        .build())
                .toList();
        var builder = symbol.toBuilder().references(references);
        if (symbol.getNamespace().equals(settings.moduleName() + ".models")
                && localNames.contains(symbol.getName())) {
            builder.namespace(partitionNamespace, ".");
        }
        return builder.build();
    }

    private void writeEnum(PythonWriter writer, EnumShape shape) {
        var enumSymbol = symbolProvider.toSymbol(shape)
                .expectProperty(SymbolProperties.ENUM_SYMBOL);
        var name = enumSymbol.getName();
        writer.addLocallyDefinedSymbol(enumSymbol);
        writer.addStdlibImport("enum", "StrEnum");
        writer.openBlock("class $L($T, StrEnum):", "", name, RuntimeTypes.UNKNOWN_ENUM_MIXIN, () -> {
            shape.getTrait(DocumentationTrait.class)
                    .ifPresent(trait -> writer.writeDocs(trait.getValue(), context));
            for (var member : shape.members()) {
                var memberName = symbolProvider.toMemberName(member);
                var value = member.expectTrait(EnumValueTrait.class).expectStringValue();
                writer.write("$L = $S", memberName, value);
                writeMemberDocs(writer, member);
            }
        });
        writer.write("");
    }

    private void writeIntEnum(PythonWriter writer, software.amazon.smithy.model.shapes.IntEnumShape shape) {
        var enumSymbol = symbolProvider.toSymbol(shape)
                .expectProperty(SymbolProperties.ENUM_SYMBOL);
        writer.addLocallyDefinedSymbol(enumSymbol);
        writer.addStdlibImport("enum", "IntEnum");
        writer.openBlock("class $L($T, IntEnum):",
                "",
                enumSymbol.getName(),
                RuntimeTypes.UNKNOWN_ENUM_MIXIN,
                () -> {
                    shape.getTrait(DocumentationTrait.class)
                            .ifPresent(trait -> writer.writeDocs(trait.getValue(), context));
                    for (var member : shape.members()) {
                        var memberName = symbolProvider.toMemberName(member);
                        var value = member.expectTrait(EnumValueTrait.class).expectIntValue();
                        writer.write("$L = $L", memberName, value);
                        writeMemberDocs(writer, member);
                    }
                });
        writer.write("");
    }

    private void writeOperation(PythonWriter writer, OperationShape shape) {
        writer.addImport("smithy_core.schemas", "APIOperation");
        var opName = symbolProvider.toSymbol(shape).getName();
        var inName = symbolProvider.toSymbol(model.expectShape(shape.getInputShape())).getName();
        var outName = symbolProvider.toSymbol(model.expectShape(shape.getOutputShape())).getName();
        writer.write("$L: APIOperation[$L, $L]", opName, inName, outName);
    }
}
