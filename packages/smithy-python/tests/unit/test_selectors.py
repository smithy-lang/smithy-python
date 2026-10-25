# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from smithy_python.exceptions import SelectorSyntaxError
from smithy_python.model import Model, load_model
from smithy_python.selection import Selector


def _model(shapes: dict[str, object]) -> Model:
    return load_model({"smithy": "2.0", "shapes": shapes})


def _select(model: Model, source: str) -> set[str]:
    return set(map(str, Selector.parse(source).select(model)))


def test_shape_types_categories_and_enum_aliases() -> None:
    model = _model(
        {
            "example#Text": {"type": "string"},
            "example#Count": {"type": "integer"},
            "example#Choice": {
                "type": "enum",
                "members": {
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "a"},
                    }
                },
            },
            "example#Numbers": {
                "type": "list",
                "member": {"target": "example#Count"},
            },
        }
    )

    assert _select(model, "number [id|namespace=example]") == {"example#Count"}
    assert _select(model, "string [id|namespace=example]") == {
        "example#Text",
        "example#Choice",
    }
    assert _select(model, "aggregateType [id|namespace=example]") == {"example#Numbers"}
    assert _select(model, "member [id|namespace=example]") == {
        "example#Choice$A",
        "example#Numbers$member",
    }


def test_attributes_projections_scopes_and_comparators() -> None:
    model = _model(
        {
            "example#Match": {
                "type": "string",
                "traits": {
                    "example#config": {
                        "enabled": True,
                        "min": 3,
                        "max": 3,
                        "mode": "foo",
                        "tags": ["internal", "external"],
                    }
                },
            },
            "example#NoMatch": {
                "type": "string",
                "traits": {
                    "example#config": {
                        "enabled": False,
                        "min": 1,
                        "max": 3,
                        "mode": "foo",
                        "tags": [],
                    }
                },
            },
        }
    )

    assert _select(model, "[trait|example#config|min >= 3]") == {"example#Match"}
    assert _select(model, "[trait|example#config|tags|(values) = external]") == {
        "example#Match"
    }
    assert _select(model, "[@trait|example#config: @{min} = @{max}]") == {
        "example#Match"
    }
    assert _select(
        model,
        "[@trait|example#config|tags|(values): @{} = external]",
    ) == {"example#Match"}
    assert _select(
        model,
        "[@trait|example#config: @{mode}=foo&&@{enabled}=true]",
    ) == {"example#Match"}
    assert _select(model, "[id|name ^= match i]") == {"example#Match"}


def test_null_trait_value_is_present() -> None:
    model = _model(
        {
            "example#Container": {
                "type": "structure",
                "members": {
                    "value": {
                        "target": "smithy.api#Document",
                        "traits": {"smithy.api#default": None},
                    }
                },
            }
        }
    )

    assert _select(model, "member [trait|default]") == {"example#Container$value"}


def test_neighbors_recursive_functions_and_variables() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "version": "1",
                "operations": [{"target": "example#Operation"}],
            },
            "example#Operation": {
                "type": "operation",
                "input": {"target": "example#Input"},
                "output": {"target": "example#Output"},
            },
            "example#Input": {
                "type": "structure",
                "members": {"value": {"target": "example#InputNumber"}},
            },
            "example#Output": {
                "type": "structure",
                "members": {"value": {"target": "example#OutputNumber"}},
            },
            "example#InputNumber": {"type": "integer"},
            "example#OutputNumber": {"type": "long"},
        }
    )

    assert _select(model, "service ~> number") == {
        "example#InputNumber",
        "example#OutputNumber",
    }
    assert _select(model, "number :test(< member < structure)") == {
        "example#InputNumber",
        "example#OutputNumber",
    }
    assert _select(
        model,
        "service $outputs(~> operation -[output]-> ~> number) "
        "~> operation -[input]-> ~> number :not(:in(${outputs}))",
    ) == {"example#InputNumber"}
    assert _select(
        model,
        "number :in(:root(service ~> operation -[output]-> ~> number))",
    ) == {"example#OutputNumber"}


def test_traits_recursive_selector_and_topdown() -> None:
    model = _model(
        {
            "example#Marker": {
                "type": "structure",
                "traits": {"smithy.api#trait": {}},
            },
            "example#Base": {
                "type": "structure",
                "traits": {"smithy.api#mixin": {}},
            },
            "example#Derived": {
                "type": "structure",
                "mixins": [{"target": "example#Base"}],
                "traits": {"smithy.api#sensitive": {}},
            },
            "example#Service": {
                "type": "service",
                "version": "1",
                "operations": [{"target": "example#Operation"}],
                "traits": {"example#Marker": {}},
            },
            "example#Operation": {
                "type": "operation",
                "traits": {"example#Marker": {}},
            },
        }
    )

    assert _select(model, "[id=example#Derived] :recursive(-[mixin]->)") == {
        "example#Base"
    }
    assert _select(model, "-[trait]-> [trait|trait] [id|namespace=example]") == {
        "example#Marker"
    }
    assert _select(
        model,
        "[id=smithy.api#sensitive] <-[trait]- structure",
    ) == {"example#Derived"}
    assert _select(model, ":topdown([trait|example#Marker])") == {
        "example#Service",
        "example#Operation",
    }


def test_virtual_prelude_traits_preserve_shape_types() -> None:
    model = _model(
        {
            "example#Data": {
                "type": "structure",
                "traits": {"smithy.api#xmlName": "renamed"},
            }
        }
    )

    assert _select(
        model,
        "structure :test(-[trait]-> string [id=smithy.api#xmlName])",
    ) == {"example#Data"}


@pytest.mark.parametrize(
    ("meta_trait", "applied_trait"),
    (
        ("smithy.api#trait", "example#Missing"),
        ("smithy.api#authDefinition", "smithy.api#httpApiKeyAuth"),
    ),
)
def test_virtual_traits_do_not_shadow_existing_meta_traits(
    meta_trait: str, applied_trait: str
) -> None:
    model = _model(
        {
            meta_trait: {
                "type": "structure",
                "members": {"value": {"target": "smithy.api#String"}},
            },
            "example#Data": {
                "type": "structure",
                "traits": {applied_trait: {}},
            },
        }
    )

    assert _select(model, f"[id={meta_trait}] > member") == {f"{meta_trait}$value"}


def test_topdown_includes_resource_operations() -> None:
    model = _model(
        {
            "example#Marker": {
                "type": "structure",
                "traits": {"smithy.api#trait": {}},
            },
            "example#Service": {
                "type": "service",
                "version": "1",
                "resources": [{"target": "example#Resource"}],
                "traits": {"example#Marker": {}},
            },
            "example#Resource": {
                "type": "resource",
                "create": {"target": "example#Create"},
                "collectionOperations": [{"target": "example#Collection"}],
            },
            "example#Create": {"type": "operation"},
            "example#Collection": {"type": "operation"},
        }
    )

    assert _select(model, ":topdown([trait|example#Marker])") == {
        "example#Service",
        "example#Resource",
        "example#Create",
        "example#Collection",
    }


def test_topdown_tracks_qualification_per_path() -> None:
    model = _model(
        {
            "example#Marker": {
                "type": "structure",
                "traits": {"smithy.api#trait": {}},
            },
            "example#Service": {
                "type": "service",
                "version": "1",
                "operations": [{"target": "example#Operation"}],
                "resources": [{"target": "example#Resource"}],
            },
            "example#Resource": {
                "type": "resource",
                "create": {"target": "example#Operation"},
                "traits": {"example#Marker": {}},
            },
            "example#Operation": {"type": "operation"},
        }
    )

    assert _select(model, ":topdown([trait|example#Marker])") == {
        "example#Resource",
        "example#Operation",
    }


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_ordered_comparisons_ignore_non_finite_values(value: str) -> None:
    model = _model(
        {
            "example#Value": {
                "type": "string",
                "traits": {"smithy.api#default": value},
            }
        }
    )

    assert _select(model, "[trait|default > 0]") == set()


def test_invalid_selector_reports_location() -> None:
    with pytest.raises(SelectorSyntaxError, match=r"line 1, column"):
        Selector.parse("structure [trait|")
