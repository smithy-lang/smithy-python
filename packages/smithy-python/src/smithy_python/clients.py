# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Client model normalization, planning, and package generation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from . import _client_emitter
from . import dependencies as _dependencies
from . import files as _files
from . import generation as _generation
from . import model as _model
from . import models as _models
from . import protocols as _protocols
from . import schemas as _schemas
from . import selection as _selection
from . import symbols as _symbols

__all__ = ["ClientGenerator", "ClientPlan", "OperationPlan", "normalize_client_model"]


class ClientGenerator:
    """Generate a client package with paired sync and async clients."""

    def __init__(
        self,
        plan: ClientPlan,
        *,
        protocols: Mapping[
            _model.ShapeId, _protocols.ProtocolContribution
        ] = _protocols.DEFAULT_PROTOCOLS,
    ) -> None:
        self._plan = plan
        self._protocols = protocols

    def generate(
        self, context: _generation.GenerationContext[_generation.ClientSettings]
    ) -> None:
        """Register every file and dependency in the generation context.

        :raises CodegenError: If no supported protocol can be selected, or the
            service needs a feature client generation does not support yet.
        """
        plan = self._plan
        service = plan.selection.service
        assert service is not None  # noqa: S101 - ClientPlan requires a service
        protocol = _protocols.select_protocol(
            service, context.settings.protocol, self._protocols
        )
        _client_emitter.check_supported(plan)
        _schemas.SchemaGenerator().generate(context)
        _models.ModelGenerator().generate(context)
        _client_emitter.write_client(context, plan, protocol)

    def context(
        self,
        dependencies: _dependencies.DependencySet | None = None,
    ) -> _generation.GenerationContext[_generation.ClientSettings]:
        """Return a generation context backed by this generator's plan."""
        plan = self._plan
        dependencies = dependencies or _dependencies.DependencySet()
        return _generation.GenerationContext(
            model=plan.model,
            selection=plan.selection,
            settings=plan.settings,
            symbols=plan.symbols,
            plan=_generation.GenerationPlan(schemas=plan.schemas, models=plan.models),
            dependencies=dependencies,
            files=_files.FileManifest(dependencies),
        )


@dataclass(frozen=True, slots=True)
class OperationPlan:
    """Names and normalized relationships for one contained operation."""

    operation: _model.OperationShape
    method_name: str
    schema_name: str
    input_name: str
    output_name: str


@dataclass(frozen=True, slots=True)
class ClientPlan:
    """A normalized service and the shared plans needed by client emitters.

    The schema plan covers selected data shapes, contained operations, and the
    service. The model plan covers data declarations and lazy operation exports.
    Planning neither writes files nor resolves a protocol implementation.
    """

    model: _model.Model
    selection: _selection.Selection
    settings: _generation.ClientSettings
    symbols: _symbols.ClientSymbolProvider
    schemas: _schemas.SchemaPlan
    models: _generation.ModelPlan
    operations: tuple[OperationPlan, ...]

    @classmethod
    def from_model(
        cls,
        model: _model.Model,
        settings: _generation.ClientSettings,
        *,
        service_id: str | None = None,
    ) -> ClientPlan:
        """Resolve a service, normalize its I/O, and plan in deterministic order."""
        selection = _selection.select_shapes(
            model, service_id=service_id, require_service=True
        )
        service = selection.service
        assert service is not None  # noqa: S101 - required service invariant
        model = normalize_client_model(model, service, package=settings.package)
        selection = _selection.select_shapes(
            model, service_id=str(service.id), require_service=True
        )
        service = model.expect_shape(service.id, _model.ServiceShape)
        operations = _selection.contained_operations(model, service)
        symbols = _symbols.ClientSymbolProvider(
            model,
            selection,
            package=settings.package,
            operations=operations,
            reserved_member_names=_models._model_reserved_member_names(model),  # pyright: ignore[reportPrivateUsage]
        )
        schemas = _schemas.SchemaPlan.from_shapes(
            model,
            (*selection.shapes, *operations, service),
            symbols,
            retained_traits=(
                *_protocols.DEFAULT_PROTOCOLS,
                *(() if settings.protocol is None else (settings.protocol,)),
            ),
        )
        operation_models = tuple(
            _generation.OperationModel(
                name=symbols.schema_name(operation.id),
                input_name=symbols.declaration_name(operation.input),
                output_name=symbols.declaration_name(operation.output),
                error_ids=operation.errors,
                auth_scheme_ids=_effective_auth_schemes(model, service, operation),
            )
            for operation in operations
        )
        return cls(
            model=model,
            selection=selection,
            settings=settings,
            symbols=symbols,
            schemas=schemas,
            models=_generation.ModelPlan.from_shapes(
                selection.shapes,
                symbols,
                schemas.names,
                operation_models,
                _input_dict_names(model, operations, symbols),
            ),
            operations=tuple(
                OperationPlan(
                    operation=operation,
                    method_name=symbols.operation_name(operation.id),
                    schema_name=symbols.schema_name(operation.id),
                    input_name=symbols.declaration_name(operation.input),
                    output_name=symbols.declaration_name(operation.output),
                )
                for operation in operations
            ),
        )


def normalize_client_model(
    model: _model.Model, service: _model.ServiceShape, *, package: str
) -> _model.Model:
    """Return a separate immutable model with dedicated operation I/O.

    Canonically named I/O with no other references can keep its ID. Shared,
    recursive, and implicitly Unit I/O get fresh structures. Source objects are
    never mutated; original shapes remain available to other references.
    """
    service = model.expect_shape(service.id, _model.ServiceShape)
    selection = _selection.select_shapes(model, service_id=str(service.id))
    operations = _selection.contained_operations(model, service)
    symbols = _symbols.ClientSymbolProvider(
        model, selection, package=package, operations=operations
    )
    references = _reference_counts(model)
    names = {name.casefold() for name in symbols.model_names()}
    shapes = dict(model.shapes)
    for operation in operations:
        io: list[_model.ShapeId] = []
        for source_id, preferred, marker in zip(
            (operation.input, operation.output),
            symbols.operation_io_names(operation.id),
            (_INPUT, _OUTPUT),
            strict=True,
        ):
            source = model.expect_shape(source_id, _model.StructureShape)
            target = _model.ShapeId(operation.id.namespace, preferred)
            normalized = source.has_trait(_ORIGINAL) and source.has_trait(marker)
            reusable = references[source.id] == 1 and (
                target == source.id or normalized
            )
            if reusable:
                target = source.id
            if not reusable:
                suffix = 2
                while target in shapes or target.name.casefold() in names:
                    target = _model.ShapeId(
                        operation.id.namespace, f"{preferred}{suffix}"
                    )
                    suffix += 1
            traits = {
                trait_id: value
                for trait_id, value in source.traits.items()
                if trait_id not in (_INPUT, _OUTPUT)
            }
            traits[_ORIGINAL] = (
                source.get_trait(_ORIGINAL)
                if source.has_trait(_ORIGINAL)
                else str(source.id)
            )
            traits[marker] = _EMPTY_TRAIT
            shapes[target] = replace(
                source,
                id=target,
                traits=MappingProxyType(traits),
                members=MappingProxyType(
                    {
                        name: replace(member, id=target.with_member(name))
                        for name, member in source.members.items()
                    }
                ),
            )
            names.add(target.name.casefold())
            io.append(target)
        shapes[operation.id] = replace(
            operation,
            input=io[0],
            output=io[1],
            errors=tuple(dict.fromkeys((*operation.errors, *service.errors))),
        )
    return _model.Model(
        smithy_version=model.smithy_version,
        metadata=model.metadata,
        shapes=shapes,
    )


_INPUT = _model.ShapeId("smithy.api", "input")
_OUTPUT = _model.ShapeId("smithy.api", "output")
_ORIGINAL = _model.ShapeId("smithy.synthetic", "originalShapeId")
_EMPTY_TRAIT: Mapping[str, _model.Node] = MappingProxyType({})
_AUTH = _model.ShapeId("smithy.api", "auth")
_AUTH_DEFINITION = _model.ShapeId("smithy.api", "authDefinition")
_OPTIONAL_AUTH = _model.ShapeId("smithy.api", "optionalAuth")
_NO_AUTH = _model.ShapeId("smithy.api", "noAuth")
# The embedded prelude omits trait definitions, so its auth traits are listed.
_PRELUDE_AUTH_SCHEMES = frozenset(
    _model.ShapeId("smithy.api", name)
    for name in ("httpApiKeyAuth", "httpBasicAuth", "httpBearerAuth", "httpDigestAuth")
)


def _effective_auth_schemes(
    model: _model.Model,
    service: _model.ServiceShape,
    operation: _model.OperationShape,
) -> tuple[_model.ShapeId, ...]:
    """Smithy's effective auth schemes in ``NO_AUTH_AWARE`` mode.

    Service schemes are ordered by shape ID unless an ``auth`` trait on the
    operation, or else the service, orders them. ``noAuth`` is appended when no
    scheme applies or the operation has ``optionalAuth``.
    """
    supported = sorted(
        (
            trait_id
            for trait_id in service.traits
            if trait_id in _PRELUDE_AUTH_SCHEMES
            or (
                (definition := model.find_shape(trait_id)) is not None
                and definition.has_trait(_AUTH_DEFINITION)
            )
        ),
        key=str,
    )
    priority = (
        operation.get_trait(_AUTH)
        if operation.has_trait(_AUTH)
        else service.get_trait(_AUTH)
    )
    schemes = (
        supported
        if not isinstance(priority, tuple)
        else [
            scheme_id
            for value in priority
            if isinstance(value, str)
            and (scheme_id := _model.ShapeId.from_string(value)) in supported
        ]
    )
    if not schemes or operation.has_trait(_OPTIONAL_AUTH):
        schemes.append(_NO_AUTH)
    return tuple(schemes)


def _reference_counts(model: _model.Model) -> Counter[_model.ShapeId]:
    counts: Counter[_model.ShapeId] = Counter()
    for shape in model.iter_shapes(include_prelude=True):
        counts.update(member.target for member in shape.members.values())
        if isinstance(shape, _model.OperationShape):
            counts.update((shape.input, shape.output, *shape.errors))
        elif isinstance(shape, _model.ServiceShape):
            counts.update(shape.errors)
        elif isinstance(shape, _model.ResourceShape):
            counts.update(shape.identifiers.values())
            counts.update(shape.properties.values())
    return counts


_DICT_SUFFIX = "Dict"


def _input_dict_names(
    model: _model.Model,
    operations: tuple[_model.OperationShape, ...],
    symbols: _symbols.ClientSymbolProvider,
) -> Mapping[_model.ShapeId, str]:
    """Name the dictionary forms of shapes reachable from operation inputs.

    A form is its model's name, then underscores until the name is free, then
    ``Dict``. Shapes are named in shape ID order and union members follow their
    union, so adding a shape renames no other form.

    CAUTION: smithy_core._dynamic_models.ModelRegistry._is_dict_name resolves
    these names at runtime by taking the suffix and underscores back off.
    """
    reachable: dict[_model.ShapeId, _model.Shape] = {}
    pending = [model.get_shape(operation.input) for operation in operations]
    while pending:
        shape = pending.pop()
        if isinstance(shape, _model.ListShape):
            pending.append(model.get_target(shape.member))
        elif isinstance(shape, _model.MapShape):
            pending.append(model.get_target(shape.value))
        elif shape.type in _DICT_TYPES and shape.id not in reachable:
            reachable[shape.id] = shape
            pending.extend(
                target
                for member in shape.members.values()
                if not _is_event_stream(target := model.get_target(member))
            )

    taken = set(symbols.model_names()) | {"ServiceError"}
    names: dict[_model.ShapeId, str] = {}

    def allocate(shape_id: _model.ShapeId, name: str) -> None:
        separator = ""
        while f"{name}{separator}{_DICT_SUFFIX}" in taken:
            separator += "_"
        names[shape_id] = f"{name}{separator}{_DICT_SUFFIX}"
        taken.add(names[shape_id])

    for shape_id in sorted(reachable, key=str):
        shape = reachable[shape_id]
        allocate(shape_id, _declaration_name(symbols, shape_id))
        if shape.type is _model.ShapeType.UNION:
            for member in shape.members.values():
                allocate(member.id, symbols.union_variant_name(member.id))
    return MappingProxyType(names)


_DICT_TYPES = frozenset({_model.ShapeType.STRUCTURE, _model.ShapeType.UNION})


def _declaration_name(
    symbols: _symbols.SymbolProvider, shape_id: _model.ShapeId
) -> str:
    return "Unit" if shape_id == _UNIT else symbols.declaration_name(shape_id)


def _is_event_stream(shape: _model.Shape) -> bool:
    return shape.type is _model.ShapeType.UNION and shape.has_trait("streaming")


_UNIT = _model.ShapeId("smithy.api", "Unit")
