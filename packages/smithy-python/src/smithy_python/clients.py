# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Client model normalization and semantic planning, without output emission."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from . import generation as _generation
from . import model as _model
from . import models as _models
from . import schemas as _schemas
from . import selection as _selection
from . import symbols as _symbols

__all__ = ["ClientPlan", "OperationPlan", "normalize_client_model"]


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

    Schema/model plans contain data shapes at this stage. Control schema names
    are reserved by ``symbols``; operation/schema emission is a subsequent phase.
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
        shared = _generation.GenerationPlan.from_selection(model, selection, symbols)
        return cls(
            model=model,
            selection=selection,
            settings=settings,
            symbols=symbols,
            schemas=shared.schemas,
            models=shared.models,
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
