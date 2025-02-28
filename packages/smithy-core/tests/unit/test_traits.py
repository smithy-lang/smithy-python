#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_core.traits import (
    DynamicTrait,
    Trait,
    ErrorTrait,
    ErrorFault,
    JSONNameTrait,
)
from smithy_core.shapes import ShapeID

import pytest


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
