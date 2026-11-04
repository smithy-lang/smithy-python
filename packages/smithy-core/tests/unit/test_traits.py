#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import pytest
from smithy_core.documents import DocumentValue
from smithy_core.prelude import UNIT
from smithy_core.shapes import ShapeID
from smithy_core.traits import (
    DefaultTrait,
    DynamicTrait,
    ErrorFault,
    ErrorTrait,
    JSONNameTrait,
    RpcV2CborTrait,
    RpcV2JsonTrait,
    Trait,
    UnitTypeTrait,
)


def test_trait_factory_constructs_dynamic_trait():
    trait_id = ShapeID("com.example#foo")
    document_value = "bar"
    trait = Trait.new(id=trait_id, value=document_value)
    assert isinstance(trait, DynamicTrait)
    assert trait.id == trait_id
    assert trait.document_value == document_value


def test_trait_factory_constructs_prelude_trait():
    trait = Trait.new(ErrorTrait.id, "client")
    assert isinstance(trait, ErrorTrait)
    assert trait.fault is ErrorFault.CLIENT


def test_trait_factory_constructs_new_trait():
    trait_id = ShapeID("com.example#newTrait")

    @dataclass(init=False, frozen=True)
    class NewTrait(Trait, id=trait_id):
        pass

    trait = Trait.new(trait_id)
    assert isinstance(trait, NewTrait)
    assert NewTrait.id is trait_id


def test_trait_factory_constructs_default_trait():
    trait = Trait.new(ShapeID("smithy.api#default"), 0)
    assert isinstance(trait, DefaultTrait)
    assert trait.value == 0


def test_unit_schema_uses_canonical_trait_id():
    trait = UNIT.get_trait(ShapeID("smithy.api#unitType"))
    assert isinstance(trait, UnitTypeTrait)


def test_cant_construct_base_trait():
    with pytest.raises(TypeError):
        Trait("foo")


def test_construct_from_dynamic_trait():
    dynamic = DynamicTrait(id=ErrorTrait.id, document_value="server")
    static = ErrorTrait(dynamic)
    assert static.fault is ErrorFault.SERVER


def test_cant_construct_trait_from_non_matching_dynamic_trait():
    dynamic = DynamicTrait(id=JSONNameTrait.id, document_value="client")
    with pytest.raises(ValueError):
        ErrorTrait(dynamic)


@pytest.mark.parametrize("trait_cls", [RpcV2CborTrait, RpcV2JsonTrait])
@pytest.mark.parametrize(
    "value, expected_http, expected_event_stream_http",
    [
        # Missing http defaults to http/1.1; missing eventStreamHttp follows http.
        (None, ("http/1.1",), ("http/1.1",)),
        ({}, ("http/1.1",), ("http/1.1",)),
        ({"http": ["h2", "http/1.1"]}, ("h2", "http/1.1"), ("h2", "http/1.1")),
        ({"http": ["http/1.1"], "eventStreamHttp": ["h2"]}, ("http/1.1",), ("h2",)),
        # An empty eventStreamHttp list is treated as unset.
        ({"http": ["h2"], "eventStreamHttp": []}, ("h2",), ("h2",)),
    ],
)
def test_rpcv2_protocol_trait_parses_http_versions(
    trait_cls: type[RpcV2CborTrait] | type[RpcV2JsonTrait],
    value: DocumentValue,
    expected_http: tuple[str, ...],
    expected_event_stream_http: tuple[str, ...],
) -> None:
    trait = trait_cls(value)
    assert trait.http == expected_http
    assert trait.event_stream_http == expected_event_stream_http

    # The factory resolves the id to the concrete class and parses the same way.
    created = Trait.new(trait_cls.id, value)
    assert isinstance(created, trait_cls)
    assert created.http == expected_http
    assert created.event_stream_http == expected_event_stream_http

    # Constructing from a DynamicTrait parses its document value.
    dynamic = DynamicTrait(id=trait_cls.id, document_value=value)
    from_dynamic = trait_cls(dynamic)
    assert from_dynamic.http == expected_http
    assert from_dynamic.event_stream_http == expected_event_stream_http


def test_rpcv2_json_trait_id() -> None:
    assert RpcV2JsonTrait.id == ShapeID("smithy.protocols#rpcv2Json")
    assert RpcV2JsonTrait.id != RpcV2CborTrait.id
