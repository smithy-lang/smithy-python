#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Conformance checks for generated model modules.

:py:func:`verify_models` introspects a generated client's ``models`` module and
asserts the runtime classes it builds on demand match the model (the compact
schemas they are built from) and, optionally, the ``models.pyi`` stub that carries
their static types. Type-correctness of the stub is NOT checked here -- that
requires a type checker (pyright over a generated usage fixture).
"""

from __future__ import annotations

import ast
import dataclasses
import datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from smithy_core._schema_compact import hydrate
from smithy_core.shapes import ShapeType
from smithy_core.traits import DefaultTrait, RequiredTrait, StreamingTrait

_SHAPE_CONSTS = ("STRUCTURE", "UNION", "ENUM", "INT_ENUM")

_INPUT = "smithy.api#input"


class ConformanceError(AssertionError):
    """A generated model class does not match its schema or stub."""


def verify_models(
    models: ModuleType,
    schemas: ModuleType,
    *,
    codec: Any | None = None,
    pyi_path: str | None = None,
) -> int:
    """Verify every model shape in ``schemas`` builds and matches its surface.

    :param models: The generated ``models`` module (lazy ``__getattr__`` build).
    :param schemas: The generated ``_private.schemas`` module.
    :param codec: Optional codec with ``serialize``/``deserialize``; when given, every
        shape is round-tripped through it. Omit for request-only protocols.
    :param pyi_path: If given, the ``models.pyi`` file is AST-parsed and its class
        field surface asserted to match the runtime classes.
    :returns: The number of shapes verified.
    :raises ConformanceError: On the first mismatch.
    """
    structs = _structures(schemas, models)
    for name, schema in structs.items():
        cls = getattr(models, name)
        _assert_fields_match_schema(name, cls, schema)
        if codec is not None:
            _assert_round_trips(name, cls, schema, models, codec)

    if pyi_path is not None:
        _assert_stub_matches(pyi_path, models, structs)

    return len(structs)


def _structures(schemas: ModuleType, models: ModuleType) -> dict[str, Any]:
    # A shape's generated symbol name usually equals its schema id name, but a
    # rename (two shapes sharing an id name in different namespaces) makes them
    # differ. The registry's rename map (symbol -> schema constant) is the
    # authoritative symbol<->schema pairing, so key each schema by the symbol
    # the client actually exposes rather than the ambiguous id name.
    const_to_symbol: dict[str, str] = {}
    registry = getattr(models, "_registry", None)
    if registry is not None:
        for symbol, const in getattr(registry, "_renames", {}).items():
            const_to_symbol[const] = symbol
    out: dict[str, Any] = {}
    for const in dir(schemas):
        if not (const.replace("_", "").isupper() and const[:1].isalpha()):
            continue
        tup = getattr(schemas, const)
        if not isinstance(tup, tuple):
            continue
        schema = hydrate(cast("tuple[Any, ...]", tup))
        if schema.shape_type == ShapeType.STRUCTURE:
            out[const_to_symbol.get(const, schema.id.name)] = schema
    return out


def _assert_fields_match_schema(name: str, cls: type, schema: Any) -> None:
    if not dataclasses.is_dataclass(cls):
        raise ConformanceError(f"{name}: built class is not a dataclass")
    field_names = {f.name for f in dataclasses.fields(cls)}
    for member in schema.members_by_index:
        if _is_event_stream_member(member):
            continue
        # a runtime field must exist for every modeled member (name derived by the
        # same ported namer the registry uses)
        from smithy_core._model_naming import member_field_name

        is_error = _is_error(schema)
        fname = member_field_name(
            member.expect_member_name(),
            is_error=is_error,
            carries_response_metadata=is_error or _is_output(schema),
            is_enum=False,
        )
        if fname not in field_names:
            raise ConformanceError(
                f"{name}: schema member {member.expect_member_name()!r} -> field "
                f"{fname!r} missing from built class {sorted(field_names)}"
            )


def _assert_round_trips(
    name: str, cls: type, schema: Any, models: ModuleType, codec: Any
) -> None:
    instance = _build_instance(cls, schema, models)
    body = codec.serialize(instance)
    rebuilt = codec.deserialize(body, cls)
    reserialized = codec.serialize(rebuilt)
    if body != reserialized:
        raise ConformanceError(
            f"{name}: round-trip mismatch\n  first: {body!r}\n  again: {reserialized!r}"
        )


def _build_instance(cls: type, schema: Any, models: ModuleType) -> Any:
    """Construct an instance filling required members with trivial values."""
    from smithy_core._model_naming import member_field_name

    kwargs: dict[str, Any] = {}
    is_error = _is_error(schema)
    for member in schema.members_by_index:
        if _is_event_stream_member(member):
            continue
        required = member.get_trait(RequiredTrait) is not None
        has_default = member.get_trait(DefaultTrait) is not None
        if not required or has_default or _is_input(schema):
            continue
        fname = member_field_name(
            member.expect_member_name(),
            is_error=is_error,
            carries_response_metadata=is_error or _is_output(schema),
            is_enum=False,
        )
        kwargs[fname] = _trivial_value(member, models)
    return cls(**kwargs)


def _trivial_value(member: Any, models: ModuleType) -> Any:
    st = member.shape_type
    simple: dict[ShapeType, Any] = {
        ShapeType.STRING: "x",
        ShapeType.BOOLEAN: False,
        ShapeType.TIMESTAMP: datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        ShapeType.BLOB: b"x",
        ShapeType.BYTE: 1,
        ShapeType.SHORT: 1,
        ShapeType.INTEGER: 1,
        ShapeType.LONG: 1,
        ShapeType.FLOAT: 1.0,
        ShapeType.DOUBLE: 1.0,
        ShapeType.BIG_INTEGER: 1,
        ShapeType.BIG_DECIMAL: Decimal(1),
        ShapeType.LIST: [],
        ShapeType.MAP: {},
    }
    if st in simple:
        return simple[st]
    if st == ShapeType.ENUM:
        return next(iter(member.expect_member_target().members))
    if st == ShapeType.INT_ENUM:
        return 1
    if st == ShapeType.STRUCTURE:
        target = member.expect_member_target()
        nested = getattr(models, target.id.name)
        return _build_instance(nested, target, models)
    if st == ShapeType.UNION:
        target = member.expect_member_target()
        first = target.members_by_index[0]
        variant = getattr(models, target.id.name + first.expect_member_name())
        return variant(value=_trivial_value(first, models))
    return None


def _assert_stub_matches(
    pyi_path: str, models: ModuleType, structs: dict[str, Any]
) -> None:
    """AST-parse models.pyi and assert its class field surface matches runtime."""
    stub_fields = _stub_fields(Path(pyi_path), set())
    for name in structs:
        if name not in stub_fields:
            raise ConformanceError(
                f"{name}: declared in schema but absent from models.pyi"
            )
        cls = getattr(models, name)
        runtime = {f.name for f in dataclasses.fields(cls)}
        inherited: set[str] = set()
        for base in cls.__mro__[1:]:
            if dataclasses.is_dataclass(base):
                inherited |= {f.name for f in dataclasses.fields(base)}
        # The stub declares locally-defined fields plus response_metadata (which the
        # runtime inherits on errors but declares on outputs). Normalize both sides to
        # "local fields, with response_metadata counted if present at runtime".
        local_runtime = (runtime - inherited) | (runtime & {"response_metadata"})
        if stub_fields[name] != local_runtime:
            raise ConformanceError(
                f"{name}: models.pyi fields {sorted(stub_fields[name])} != "
                f"runtime local fields {sorted(local_runtime)}"
            )


def _stub_fields(path: Path, visited: set[Path]) -> dict[str, set[str]]:
    path = path.resolve()
    if path in visited:
        return {}
    visited.add(path)

    tree = ast.parse(path.read_text())
    stub_fields: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            stub_fields[node.name] = {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
        elif isinstance(node, ast.ImportFrom) and node.level and node.module:
            base = path.parent
            for _ in range(node.level - 1):
                base = base.parent
            imported_path = base.joinpath(*node.module.split(".")).with_suffix(".pyi")
            if not imported_path.exists():
                continue
            imported = _stub_fields(imported_path, visited)
            for name in node.names:
                if name.name == "*":
                    stub_fields.update(imported)
                elif name.name in imported:
                    stub_fields[name.asname or name.name] = imported[name.name]
    return stub_fields


def _is_error(schema: Any) -> bool:
    from smithy_core.traits import ErrorTrait

    return schema.get_trait(ErrorTrait) is not None


def _is_output(schema: Any) -> bool:
    from smithy_core.shapes import ShapeID

    return schema.get_trait(ShapeID("smithy.api#output")) is not None


def _is_input(schema: Any) -> bool:
    from smithy_core.shapes import ShapeID

    return schema.get_trait(ShapeID("smithy.api#input")) is not None


def _is_event_stream_member(member: Any) -> bool:
    target = member.expect_member_target()
    return (
        target.shape_type is ShapeType.UNION
        and target.get_trait(StreamingTrait) is not None
    )
