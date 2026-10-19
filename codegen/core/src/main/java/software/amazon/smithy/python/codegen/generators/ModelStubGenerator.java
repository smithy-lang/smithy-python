/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.List;
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
import software.amazon.smithy.model.traits.EnumValueTrait;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
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

    private final GenerationContext context;
    private final PythonSettings settings;
    private final Model model;
    private final SymbolProvider symbolProvider;
    private final List<Shape> shapes;

    public ModelStubGenerator(GenerationContext context, List<Shape> shapes) {
        this.context = context;
        this.settings = context.settings();
        this.model = context.model();
        this.symbolProvider = context.symbolProvider();
        this.shapes = shapes;
    }

    @Override
    public void run() {
        var module = settings.moduleName();
        var filename = String.format("src/%s/models.pyi", module);
        var namespace = String.format("%s.models", module);

        context.writerDelegator().useFileWriter(filename, namespace, writer -> {
            writer.addStdlibImport("dataclasses", "dataclass");
            writer.addStdlibImports("typing", java.util.Set.of("Union", "Self"));
            writer.addImport("smithy_core.schemas", "APIOperation");
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
                        ...
                    """);

            for (var shape : shapes) {
                switch (shape.getType()) {
                    case STRUCTURE -> writeStruct(writer, shape.asStructureShape().get());
                    case UNION -> writeUnion(writer, shape.asUnionShape().get());
                    case ENUM -> writeEnum(writer, shape.asEnumShape().get());
                    case INT_ENUM -> writeIntEnum(writer, shape.asIntEnumShape().get());
                    default -> {
                    }
                }
            }
            for (var shape : shapes) {
                if (shape.isOperationShape()) {
                    writeOperation(writer, shape.asOperationShape().get());
                }
            }
        });
    }

    private void writeStruct(PythonWriter writer, StructureShape shape) {
        var symbol = symbolProvider.toSymbol(shape);
        var name = symbol.getName();
        writer.addLocallyDefinedSymbol(symbol);
        var isError = shape.hasTrait(ErrorTrait.class);
        var base = isError
                ? "(ServiceError, _SerdeShape)"
                : "(_SerdeShape)";
        var index = NullableIndex.of(model);
        writer.openBlock("@dataclass(kw_only=True)\nclass $L$L:", "", name, base, () -> {
            var members = shape.members()
                    .stream()
                    .filter(m -> !CodegenUtils.isErrorMessage(model, m))
                    .toList();
            if (members.isEmpty() && !carriesResponseMetadata(shape)) {
                writer.write("pass");
                return;
            }
            for (var member : members) {
                var memberName = symbolProvider.toMemberName(member);
                var mandatory = CodegenUtils.isRequiredMember(index, member)
                        && !OperationIndex.of(model).isInputStructure(shape);
                if (mandatory) {
                    writer.write("$L: $T", memberName, memberTypeSymbol(member));
                } else {
                    writer.write("$L: $T | None = ...", memberName, memberTypeSymbol(member));
                }
            }
            if (carriesResponseMetadata(shape)) {
                writer.write("response_metadata: $T = ...", RuntimeTypes.RESPONSE_METADATA);
            }
        });
        writer.write("");
    }

    private boolean carriesResponseMetadata(Shape shape) {
        return shape.hasTrait(ErrorTrait.class) || OperationIndex.of(model).isOutputStructure(shape);
    }

    private void writeUnion(PythonWriter writer, UnionShape shape) {
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
                    () -> writer.write("value: $T", valueTypeSymbol(target)));
            writer.write("");
        }
        var unknownSymbol = parentSymbol.expectProperty(SymbolProperties.UNION_UNKNOWN);
        var unknownName = unknownSymbol.getName();
        writer.addLocallyDefinedSymbol(unknownSymbol);
        writer.openBlock(
                "@dataclass\nclass $L(_SerdeShape):",
                "",
                unknownName,
                () -> writer.write("tag: str"));
        writer.write("");
        variantNames.add(unknownName);
        writer.write("$L = Union[$L]", parentName, String.join(" | ", variantNames));
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

    private void writeEnum(PythonWriter writer, EnumShape shape) {
        var enumSymbol = symbolProvider.toSymbol(shape)
                .expectProperty(SymbolProperties.ENUM_SYMBOL);
        var name = enumSymbol.getName();
        writer.addLocallyDefinedSymbol(enumSymbol);
        writer.addStdlibImport("enum", "StrEnum");
        writer.openBlock("class $L($T, StrEnum):", "", name, RuntimeTypes.UNKNOWN_ENUM_MIXIN, () -> {
            for (var member : shape.members()) {
                var memberName = symbolProvider.toMemberName(member);
                var value = member.expectTrait(EnumValueTrait.class).expectStringValue();
                writer.write("$L = $S", memberName, value);
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
                    for (var member : shape.members()) {
                        var memberName = symbolProvider.toMemberName(member);
                        var value = member.expectTrait(EnumValueTrait.class).expectIntValue();
                        writer.write("$L = $L", memberName, value);
                    }
                });
        writer.write("");
    }

    private void writeOperation(PythonWriter writer, OperationShape shape) {
        var opName = symbolProvider.toSymbol(shape).getName();
        var inName = symbolProvider.toSymbol(model.expectShape(shape.getInputShape())).getName();
        var outName = symbolProvider.toSymbol(model.expectShape(shape.getOutputShape())).getName();
        writer.write("$L: APIOperation[$L, $L]", opName, inName, outName);
    }
}
