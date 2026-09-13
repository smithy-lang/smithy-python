# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from smithy_python.exceptions import CodegenError, ModelError
from smithy_python.model import Model, ShapeID, ShapeType


def test_model_error_is_a_codegen_error() -> None:
    assert issubclass(ModelError, CodegenError)


class TestShapeID:
    def test_parse_shape_and_member_ids(self) -> None:
        assert ShapeID.parse("example#Foo") == ShapeID("example", "Foo")
        assert ShapeID.parse("example#Foo$bar") == ShapeID("example", "Foo", "bar")

    @pytest.mark.parametrize(
        "value",
        ["Foo", "#Foo", "example#", "a#b#c", "example#Foo$", "example#F$o$o", "a-b#C"],
    )
    def test_parse_rejects_invalid_ids(self, value: str) -> None:
        with pytest.raises(ModelError, match="shape ID"):
            ShapeID.parse(value)

    def test_round_trips_through_str(self) -> None:
        for value in ("example#Foo", "example.nested#Foo$bar"):
            assert str(ShapeID.parse(value)) == value

    def test_member_helpers(self) -> None:
        shape = ShapeID.parse("example#Foo")
        member = shape.with_member("bar")
        assert member.member == "bar"
        assert member.without_member() == shape
        assert shape.without_member() is shape
        assert ShapeID.parse("smithy.api#String").is_prelude
        assert not shape.is_prelude

    def test_shape_and_member_ids_sort_together(self) -> None:
        ids = [
            ShapeID.parse("b#A"),
            ShapeID.parse("a#B$c"),
            ShapeID.parse("a#B"),
            ShapeID.parse("a#A"),
        ]
        assert [str(shape_id) for shape_id in sorted(ids)] == [
            "a#A",
            "a#B",
            "a#B$c",
            "b#A",
        ]
        assert ShapeID.parse("a#B") >= ShapeID.parse("a#A$c")


class TestParsing:
    def test_preserves_shape_member_and_trait_order(self, model: Model) -> None:
        assert [shape.id.name for shape in model][:3] == [
            "CityId",
            "Coordinates",
            "Tags",
        ]
        coordinates = model.expect("example.weather#Coordinates")
        assert [member.name for member in coordinates.members] == [
            "latitude",
            "longitude",
        ]
        assert coordinates.type is ShapeType.STRUCTURE
        assert coordinates.member("latitude").has_trait("smithy.api#required")

    def test_parsed_objects_are_immutable(self, model: Model) -> None:
        coordinates = model.expect("example.weather#Coordinates")
        with pytest.raises(TypeError):
            coordinates.traits["example#trait"] = {}  # type: ignore[index]

    def test_nested_values_are_immutable(self, model: Model) -> None:
        http = model.expect("example.weather#GetCity").trait("smithy.api#http")
        assert isinstance(http, Mapping)
        with pytest.raises(TypeError):
            http["method"] = "POST"  # type: ignore[index]
        errors = model.expect("example.weather#GetCity").attributes["errors"]
        assert isinstance(errors, tuple)
        assert model.metadata["example"] is True

    def test_from_json_accepts_bytes(self, model_json: bytes, model: Model) -> None:
        assert Model.from_json(model_json) == model

    def test_len_and_metadata(self, model: Model) -> None:
        assert len(model) == 9
        assert model.metadata == {"example": True}

    def test_operation_attributes_are_kept_losslessly(self, model: Model) -> None:
        operation = model.expect("example.weather#GetCity")
        assert operation.attributes["input"] == {
            "target": "example.weather#GetCityInput"
        }
        assert operation.trait("smithy.api#http") == {
            "method": "GET",
            "uri": "/city/{cityId}",
            "code": 200,
        }

    def test_references_follow_structural_relationships(self, model: Model) -> None:
        service = model.expect("example.weather#Weather")
        assert service.references() == (ShapeID.parse("example.weather#GetCity"),)
        operation = model.expect("example.weather#GetCity")
        assert set(operation.references()) == {
            ShapeID.parse("example.weather#GetCityInput"),
            ShapeID.parse("example.weather#GetCityOutput"),
            ShapeID.parse("example.weather#NoSuchCity"),
        }

    def test_resources_and_maps_are_parsed(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#Forecasts"] = {
            "type": "map",
            "key": {"target": "example.weather#CityId"},
            "value": {"target": "smithy.api#String"},
        }
        shapes["example.weather#City"] = {
            "type": "resource",
            "identifiers": {"cityId": {"target": "example.weather#CityId"}},
            "properties": {"coordinates": {"target": "example.weather#Coordinates"}},
            "read": {"target": "example.weather#GetCity"},
            "collectionOperations": [],
        }
        model = Model.from_dict(model_document)

        forecasts = model.expect("example.weather#Forecasts")
        assert [member.name for member in forecasts.members] == ["key", "value"]
        assert forecasts.member("key").target == ShapeID.parse("example.weather#CityId")

        city = model.expect("example.weather#City")
        assert city.references() == (
            ShapeID.parse("example.weather#GetCity"),
            ShapeID.parse("example.weather#CityId"),
            ShapeID.parse("example.weather#Coordinates"),
        )

    def test_references_report_malformed_targets(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#GetCity"]["errors"] = [{"target": 1}]
        with pytest.raises(ModelError, match="Expected a shape reference"):
            Model.from_dict(model_document).expect(
                "example.weather#GetCity"
            ).references()

    def test_references_report_malformed_identifiers(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#City"] = {
            "type": "resource",
            "identifiers": [{"target": "example.weather#CityId"}],
        }
        with pytest.raises(ModelError, match="Expected an object at"):
            Model.from_dict(model_document).expect("example.weather#City").references()

    def test_apply_merges_traits_onto_members(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#Coordinates$latitude"] = {
            "type": "apply",
            "traits": {"smithy.api#documentation": "Latitude"},
        }

        model = Model.from_dict(model_document)
        latitude = model.expect("example.weather#Coordinates").member("latitude")
        assert latitude.trait("smithy.api#documentation") == "Latitude"
        assert latitude.has_trait("smithy.api#required")

    def test_apply_to_missing_member_is_an_error(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#Coordinates$altitude"] = {
            "type": "apply",
            "traits": {},
        }
        with pytest.raises(ModelError, match="Apply target member not found"):
            Model.from_dict(model_document)

    def test_apply_to_missing_target_is_an_error(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#Missing$foo"] = {
            "type": "apply",
            "traits": {},
        }
        with pytest.raises(ModelError, match="Apply target not found"):
            Model.from_dict(model_document)

    def test_apply_must_target_a_member(self, model_document: dict[str, Any]) -> None:
        model_document["shapes"]["example.weather#Other"] = {
            "type": "apply",
            "traits": {"smithy.api#documentation": "docs"},
        }
        with pytest.raises(ModelError, match="apply statement to target a member"):
            Model.from_dict(model_document)

    def test_shapes_key_is_optional(self) -> None:
        assert len(Model.from_dict({"smithy": "2.0"})) == 0

    @pytest.mark.parametrize(
        ("document", "message"),
        [
            ({}, "missing a string 'smithy' version"),
            ({"smithy": 2}, "missing a string 'smithy' version"),
            ({"smithy": "2.0", "shapes": []}, "Expected an object"),
            (
                {"smithy": "2.0", "shapes": {"example#Bad": {"type": "nope"}}},
                "Unsupported shape type",
            ),
            (
                {"smithy": "2.0", "shapes": {"example#Bad": {"type": "list"}}},
                "Expected an object at member",
            ),
            (
                {
                    "smithy": "2.0",
                    "shapes": {"example#Bad": {"type": "list", "member": {}}},
                },
                "shape target",
            ),
            (
                {
                    "smithy": "2.0",
                    "shapes": {
                        "example#Bad": {"type": "structure", "mixins": "example#M"}
                    },
                },
                "Expected a list",
            ),
            (
                {"smithy": "2.0", "shapes": {1: {"type": "string"}}},
                "Expected string object keys",
            ),
            (
                {
                    "smithy": "2.0",
                    "shapes": {
                        "example#Bad": {
                            "type": "string",
                            "traits": {"example#trait": object()},
                        }
                    },
                },
                "Unsupported JSON value",
            ),
        ],
    )
    def test_invalid_documents_are_reported(
        self, document: dict[str, Any], message: str
    ) -> None:
        with pytest.raises(ModelError, match=message):
            Model.from_dict(document)

    @pytest.mark.parametrize("source", [b"", b"not json", b"[]", b"\xff"])
    def test_invalid_json_is_reported(self, source: bytes) -> None:
        with pytest.raises(ModelError, match="Smithy JSON AST"):
            Model.from_json(source)


class TestLookup:
    def test_resolves_prelude_without_inserting_it(self, model: Model) -> None:
        assert model.expect("smithy.api#String").type is ShapeType.STRING
        assert not model.expect("smithy.api#String").traits
        unit = model.expect("smithy.api#Unit")
        assert unit.type is ShapeType.STRUCTURE
        assert unit.has_trait("smithy.api#unitType")
        assert (
            model.expect("smithy.api#PrimitiveInteger").trait("smithy.api#default") == 0
        )
        assert (
            model.expect("smithy.api#PrimitiveBoolean").trait("smithy.api#default")
            is False
        )
        assert all(not shape.id.is_prelude for shape in model)

    def test_modeled_prelude_takes_precedence(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["smithy.api#String"] = {
            "type": "string",
            "traits": {"smithy.api#documentation": "from the prelude"},
        }
        model = Model.from_dict(model_document)
        assert model.expect("smithy.api#String").has_trait("smithy.api#documentation")

    def test_get_returns_none_for_unknown_shapes(self, model: Model) -> None:
        assert model.get("example.weather#Nope") is None
        assert model.get("smithy.api#Nope") is None

    def test_prelude_shapes_are_shared_between_lookups(self, model: Model) -> None:
        assert model.expect("smithy.api#String") is model.expect("smithy.api#String")

    def test_member_id_resolves_to_container(self, model: Model) -> None:
        shape = model.expect("example.weather#Coordinates$latitude")
        assert shape.id == ShapeID.parse("example.weather#Coordinates")
        assert model.expect("example.weather#Tags$member").type is ShapeType.LIST

    def test_member_id_of_an_undefined_member_does_not_resolve(
        self, model: Model
    ) -> None:
        assert model.get("example.weather#Coordinates$altitude") is None
        assert model.get("example.weather#Nope$latitude") is None
        # The prelude resolves, but its shapes declare no members.
        assert model.get("smithy.api#Unit$value") is None

    def test_expect_reports_missing_shapes(self, model: Model) -> None:
        with pytest.raises(ModelError, match="Shape not found"):
            model.expect("example.weather#Nope")
        with pytest.raises(ModelError, match="Member not found"):
            model.expect("example.weather#Coordinates").member("altitude")

    def test_services_are_listed_in_model_order(self, model: Model) -> None:
        assert [shape.id.name for shape in model.services()] == ["Weather"]

    def test_duplicate_shapes_are_rejected(self, model: Model) -> None:
        with pytest.raises(ModelError, match="Duplicate shape"):
            model.replace_shapes((*model.shapes, model.shapes[0]))


class TestMixins:
    @staticmethod
    def _document(shapes: dict[str, Any]) -> dict[str, Any]:
        return {"smithy": "2.0", "shapes": shapes}

    def test_inherited_members_precede_local_members_depth_first(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#FilteredByName": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "members": {"nameFilter": {"target": "smithy.api#String"}},
                    },
                    "example#Paginated": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "members": {
                            "nextToken": {"target": "smithy.api#String"},
                            "pageSize": {"target": "smithy.api#Integer"},
                        },
                    },
                    "example#ListInput": {
                        "type": "structure",
                        "mixins": [
                            {"target": "example#Paginated"},
                            {"target": "example#FilteredByName"},
                        ],
                        "members": {"sizeFilter": {"target": "smithy.api#Integer"}},
                    },
                }
            )
        )
        shape = model.expect("example#ListInput")
        assert [member.name for member in shape.members] == [
            "nextToken",
            "pageSize",
            "nameFilter",
            "sizeFilter",
        ]
        assert shape.mixins == (
            ShapeID.parse("example#Paginated"),
            ShapeID.parse("example#FilteredByName"),
        )
        # Mixins themselves are left untouched.
        assert len(model.expect("example#Paginated").members) == 2

    def test_traits_are_inherited_with_local_and_later_precedence(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#A": {
                        "type": "structure",
                        "traits": {
                            "smithy.api#mixin": {"localTraits": ["smithy.api#private"]},
                            "smithy.api#private": {},
                            "smithy.api#documentation": "A",
                            "example#foo": 1,
                            "example#onlyA": True,
                        },
                    },
                    "example#B": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}, "example#foo": 2},
                    },
                    "example#C": {
                        "type": "structure",
                        "mixins": [{"target": "example#A"}, {"target": "example#B"}],
                        "traits": {
                            "smithy.api#mixin": {},
                            "smithy.api#documentation": "C",
                        },
                    },
                    "example#D": {
                        "type": "structure",
                        "mixins": [{"target": "example#C"}],
                    },
                }
            )
        )
        c = model.expect("example#C")
        assert c.trait("smithy.api#documentation") == "C"
        assert c.trait("example#foo") == 2
        assert c.has_trait("example#onlyA")
        assert not c.has_trait("smithy.api#private")
        # Inheritance is transitive, and the mixin trait itself is not inherited.
        d = model.expect("example#D")
        assert d.trait("smithy.api#documentation") == "C"
        assert d.trait("example#foo") == 2
        assert d.has_trait("example#onlyA")
        assert not d.has_trait("smithy.api#private")
        assert not d.has_trait("smithy.api#mixin")

    def test_apply_targets_inherited_members(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#M": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "members": {"foo": {"target": "smithy.api#String"}},
                    },
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                    },
                    "example#S$foo": {
                        "type": "apply",
                        "traits": {"smithy.api#required": {}},
                    },
                    "example#M$foo": {
                        "type": "apply",
                        "traits": {"smithy.api#documentation": "docs"},
                    },
                }
            )
        )
        foo = model.expect("example#S").member("foo")
        assert foo.has_trait("smithy.api#required")
        assert foo.trait("smithy.api#documentation") == "docs"
        assert (
            not model.expect("example#M").member("foo").has_trait("smithy.api#required")
        )

    def test_apply_on_intermediate_mixin_propagates_to_users(self) -> None:
        # A <- B <- C, with an apply on B$foo, which B inherits from A.
        model = Model.from_dict(
            self._document(
                {
                    "example#A": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "members": {"foo": {"target": "smithy.api#String"}},
                    },
                    "example#B": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "mixins": [{"target": "example#A"}],
                    },
                    "example#C": {
                        "type": "structure",
                        "mixins": [{"target": "example#B"}],
                    },
                    "example#B$foo": {
                        "type": "apply",
                        "traits": {"smithy.api#required": {}},
                    },
                }
            )
        )
        assert model.expect("example#B").member("foo").has_trait("smithy.api#required")
        assert model.expect("example#C").member("foo").has_trait("smithy.api#required")
        assert (
            not model.expect("example#A").member("foo").has_trait("smithy.api#required")
        )

    def test_inherited_values_cannot_be_mutated_through_a_sibling(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#M": {
                        "type": "structure",
                        "traits": {
                            "smithy.api#mixin": {},
                            "smithy.api#tags": ["shared"],
                            "smithy.api#http": {"method": "GET", "uri": "/"},
                        },
                    },
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                    },
                    "example#T": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                    },
                }
            )
        )
        s_http = model.expect("example#S").trait("smithy.api#http")
        assert isinstance(s_http, Mapping)
        with pytest.raises(TypeError):
            s_http["method"] = "POST"  # type: ignore[index]
        tags = model.expect("example#S").trait("smithy.api#tags")
        assert isinstance(tags, tuple)
        assert model.expect("example#T").trait("smithy.api#http") == {
            "method": "GET",
            "uri": "/",
        }

    def test_redefined_members_merge_traits_and_keep_position(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#M": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "members": {
                            "a": {
                                "target": "smithy.api#String",
                                "traits": {"smithy.api#documentation": "docs"},
                            },
                            "b": {"target": "smithy.api#String"},
                        },
                    },
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                        "members": {
                            "c": {"target": "smithy.api#String"},
                            "a": {
                                "target": "smithy.api#String",
                                "traits": {"smithy.api#required": {}},
                            },
                        },
                    },
                }
            )
        )
        shape = model.expect("example#S")
        assert [member.name for member in shape.members] == ["a", "b", "c"]
        a = shape.member("a")
        assert a.has_trait("smithy.api#required")
        assert a.has_trait("smithy.api#documentation")

    def test_list_and_map_members_are_inherited(self) -> None:
        # Smithy omits member, key, and value from a shape that inherits them.
        model = Model.from_dict(
            self._document(
                {
                    "example#AbstractList": {
                        "type": "list",
                        "traits": {"smithy.api#mixin": {}},
                        "member": {"target": "smithy.api#String"},
                    },
                    "example#Names": {
                        "type": "list",
                        "mixins": [{"target": "example#AbstractList"}],
                    },
                    "example#AbstractMap": {
                        "type": "map",
                        "traits": {"smithy.api#mixin": {}},
                        "key": {"target": "smithy.api#String"},
                        "value": {"target": "smithy.api#Integer"},
                    },
                    "example#Counts": {
                        "type": "map",
                        "mixins": [{"target": "example#AbstractMap"}],
                    },
                    "example#Names$member": {
                        "type": "apply",
                        "traits": {"smithy.api#documentation": "A name"},
                    },
                }
            )
        )
        names = model.expect("example#Names")
        assert names.member("member").target == ShapeID.parse("smithy.api#String")
        assert names.member("member").trait("smithy.api#documentation") == "A name"

        counts = model.expect("example#Counts")
        assert [member.name for member in counts.members] == ["key", "value"]
        assert counts.member("value").target == ShapeID.parse("smithy.api#Integer")

    def test_redefined_members_must_keep_their_target(self) -> None:
        with pytest.raises(ModelError, match="different target"):
            Model.from_dict(
                self._document(
                    {
                        "example#M": {
                            "type": "structure",
                            "traits": {"smithy.api#mixin": {}},
                            "members": {"a": {"target": "smithy.api#String"}},
                        },
                        "example#S": {
                            "type": "structure",
                            "mixins": [{"target": "example#M"}],
                            "members": {"a": {"target": "smithy.api#Integer"}},
                        },
                    }
                )
            )

    def test_service_properties_are_merged(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#A": {
                        "type": "service",
                        "version": "A",
                        "operations": [{"target": "example#OpA"}],
                        "traits": {"smithy.api#mixin": {}},
                    },
                    "example#B": {
                        "type": "service",
                        "version": "B",
                        "rename": {"example#X": "Y"},
                        "operations": [{"target": "example#OpB"}],
                        "mixins": [{"target": "example#A"}],
                        "traits": {"smithy.api#mixin": {}},
                    },
                    "example#C": {
                        "type": "service",
                        "version": "C",
                        "rename": {"example#Z": "W"},
                        "operations": [
                            {"target": "example#OpC"},
                            {"target": "example#OpA"},
                        ],
                        "mixins": [{"target": "example#B"}],
                    },
                    "example#OpA": {"type": "operation"},
                    "example#OpB": {"type": "operation"},
                    "example#OpC": {"type": "operation"},
                }
            )
        )
        service = model.expect("example#C")
        assert service.attributes["version"] == "C"
        assert service.attributes["rename"] == {"example#X": "Y", "example#Z": "W"}
        assert service.references() == (
            ShapeID.parse("example#B"),
            ShapeID.parse("example#OpA"),
            ShapeID.parse("example#OpB"),
            ShapeID.parse("example#OpC"),
        )

    def test_operation_errors_are_inherited(self) -> None:
        model = Model.from_dict(
            self._document(
                {
                    "example#Validated": {
                        "type": "operation",
                        "errors": [{"target": "example#ValidationError"}],
                        "traits": {"smithy.api#mixin": {}},
                    },
                    "example#GetUser": {
                        "type": "operation",
                        "errors": [{"target": "example#NotFound"}],
                        "mixins": [{"target": "example#Validated"}],
                    },
                    "example#ValidationError": {
                        "type": "structure",
                        "traits": {"smithy.api#error": "client"},
                    },
                    "example#NotFound": {
                        "type": "structure",
                        "traits": {"smithy.api#error": "client"},
                    },
                }
            )
        )
        assert model.expect("example#GetUser").attributes["errors"] == (
            {"target": "example#ValidationError"},
            {"target": "example#NotFound"},
        )

    @pytest.mark.parametrize(
        ("shapes", "message"),
        [
            (
                {
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#Missing"}],
                    }
                },
                "Mixin not found",
            ),
            (
                {
                    "example#M": {"type": "structure"},
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                    },
                },
                "lacks the smithy.api#mixin trait",
            ),
            (
                {
                    "example#M": {
                        "type": "list",
                        "traits": {"smithy.api#mixin": {}},
                        "member": {"target": "smithy.api#String"},
                    },
                    "example#S": {
                        "type": "structure",
                        "mixins": [{"target": "example#M"}],
                    },
                },
                "is a structure but uses the list shape",
            ),
            (
                {
                    "example#A": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "mixins": [{"target": "example#B"}],
                    },
                    "example#B": {
                        "type": "structure",
                        "traits": {"smithy.api#mixin": {}},
                        "mixins": [{"target": "example#A"}],
                    },
                },
                "Mixin cycle",
            ),
        ],
    )
    def test_invalid_mixins_are_reported(
        self, shapes: dict[str, Any], message: str
    ) -> None:
        with pytest.raises(ModelError, match=message):
            Model.from_dict(self._document(shapes))
