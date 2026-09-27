# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json

import pytest
from smithy_python.model import MemberShape, Model, load_model
from smithy_python.selection import select_shapes
from smithy_python.symbols import SymbolProvider


def model_with(shapes: dict[str, object]) -> Model:
    return load_model(json.dumps({"smithy": "2.0", "shapes": shapes}))


@pytest.mark.parametrize(
    ("source", "declaration", "field", "constant"),
    [
        ("HTTPServer", "HttpServer", "http_server", "HTTP_SERVER"),
        ("getURL", "GetUrl", "get_url", "GET_URL"),
        ("HTTP2Server", "Http2Server", "http2_server", "HTTP2_SERVER"),
        ("getURL2Value", "GetUrl2Value", "get_url2_value", "GET_URL2_VALUE"),
        ("__some__name__", "SomeName", "some_name", "SOME_NAME"),
        ("__init__", "Init", "init", "INIT"),
        ("_value", "Value", "value", "VALUE"),
        ("class", "Class", "class_", "CLASS"),
        ("None", "None_", "none", "NONE"),
        ("match", "Match", "match", "MATCH"),
    ],
)
def test_names(source: str, declaration: str, field: str, constant: str) -> None:
    model = model_with(
        {
            f"example#{source}": {
                "type": "structure",
                "members": {source: {"target": "smithy.api#String"}},
            },
            "example#Choice": {
                "type": "enum",
                "members": {
                    source: {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "wire"},
                    }
                },
            },
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="example.client")
    assert symbols.declaration_name(f"example#{source}") == declaration
    assert symbols.member_name(f"example#{source}${source}") == field
    assert symbols.member_name(f"example#Choice${source}") == constant
    assert model.get_shape(f"example#{source}").id.name == source
    assert model.get_shape(f"example#Choice${source}").get_trait("enumValue") == "wire"


@pytest.mark.parametrize(
    ("kind", "name", "module"),
    [
        ("boolean", "bool", "builtins"),
        ("string", "str", "builtins"),
        *[
            (kind, "int", "builtins")
            for kind in ("byte", "short", "integer", "long", "bigInteger")
        ],
        ("float", "float", "builtins"),
        ("double", "float", "builtins"),
        ("blob", "bytes", "builtins"),
        ("bigDecimal", "Decimal", "decimal"),
        ("timestamp", "datetime", "datetime"),
        ("document", "Document", "smithy_core.documents"),
        *[
            (kind, "HttpServer", "example.client.models")
            for kind in ("structure", "union", "enum", "intEnum")
        ],
    ],
)
def test_type_references(kind: str, name: str, module: str) -> None:
    from dataclasses import FrozenInstanceError

    from smithy_python.symbols import TypeReference

    model = model_with({"example#HTTPServer": {"type": kind}})
    symbols = SymbolProvider(model, select_shapes(model), package="example.client")
    ref = symbols.type_reference("example#HTTPServer")
    assert ref == TypeReference(name, module)
    assert hash(ref) == hash(TypeReference(name, module))
    with pytest.raises(FrozenInstanceError):
        setattr(ref, "name", "Changed")
    if module != "example.client.models":
        prelude_name = kind[0].upper() + kind[1:]
        assert symbols.type_reference(f"smithy.api#{prelude_name}") == ref
    assert symbols.type_reference("smithy.api#Unit") == TypeReference("None")


def test_service_rename_only_changes_declaration() -> None:
    from smithy_python.selection import Selection
    from smithy_python.symbols import TypeReference

    model = model_with(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Op"}],
                "rename": {"example#Original": "HTTPServer"},
            },
            "example#Op": {
                "type": "operation",
                "input": {"target": "example#Original"},
            },
            "example#Original": {"type": "structure"},
        }
    )
    selection = select_shapes(model)
    symbols = SymbolProvider(model, selection, package="pkg")
    assert symbols.declaration_name("example#Original") == "HttpServer"
    assert symbols.type_reference("example#Original") == TypeReference(
        "HttpServer", "pkg.models"
    )
    without_service = SymbolProvider(
        model, Selection(None, selection.shapes, 0), package="pkg"
    )
    assert without_service.declaration_name("example#Original") == "Original"
    assert str(selection.shapes[0].id) == "example#Original"


@pytest.mark.parametrize("sparse", [False, True])
def test_collections_and_recursive_named_types(sparse: bool) -> None:
    from smithy_python.symbols import TypeReference

    traits: dict[str, object] = {"smithy.api#sparse": {}} if sparse else {}
    model = model_with(
        {
            "example#Nodes": {
                "type": "list",
                "member": {"target": "example#Node"},
                "traits": traits,
            },
            "example#Index": {
                "type": "map",
                "key": {"target": "smithy.api#String"},
                "value": {"target": "example#Nodes"},
                "traits": traits,
            },
            "example#Node": {
                "type": "structure",
                "members": {
                    "self": {"target": "example#Node"},
                    "children": {"target": "example#Index"},
                    "other": {"target": "example#Other"},
                    "required": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#required": {}},
                    },
                    "defaulted": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#default": ""},
                    },
                },
            },
            "example#Other": {
                "type": "union",
                "members": {"node": {"target": "example#Node"}},
            },
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    node = TypeReference("Node", "pkg.models")
    nodes = TypeReference(
        "list", "builtins", (TypeReference("Node", "pkg.models", nullable=sparse),)
    )
    index = TypeReference(
        "dict",
        "builtins",
        (
            TypeReference("str", "builtins"),
            TypeReference("list", "builtins", nodes.arguments, nullable=sparse),
        ),
    )
    expected = {
        "example#Node": node,
        "example#Nodes": nodes,
        "example#Index": index,
        "example#Other": TypeReference("Other", "pkg.models"),
    }
    for order in (tuple(expected), tuple(reversed(expected))):
        for shape_id in order:
            assert symbols.type_reference(shape_id) == expected[shape_id]
    for member in ("required", "defaulted"):
        target = model.expect_shape(f"example#Node${member}", MemberShape).target
        assert symbols.type_reference(target) == TypeReference("str", "builtins")


@pytest.mark.parametrize("mutual", [False, True])
def test_collection_only_cycles(mutual: bool) -> None:
    from smithy_python.model import ModelError

    model = model_with(
        {
            "example#Loop": {
                "type": "list",
                "member": {"target": "example#Map" if mutual else "example#Loop"},
            },
            "example#Map": {
                "type": "map",
                "key": {"target": "smithy.api#String"},
                "value": {"target": "example#Loop"},
            },
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    for shape_id in ("example#Loop", "example#Map", "example#Loop"):
        with pytest.raises(ModelError, match=r"Collection-only cycle.*example#Loop"):
            symbols.type_reference(shape_id)


@pytest.mark.parametrize("kind", ["structure", "union", "enum", "intEnum"])
@pytest.mark.parametrize(
    "names", [("getURL", "get_url"), ("class", "class_"), ("__init__", "init")]
)
def test_member_collisions(kind: str, names: tuple[str, str]) -> None:
    from smithy_python.model import ModelError

    model = model_with(
        {
            "example#Container": {
                "type": kind,
                "members": {name: {"target": "smithy.api#Unit"} for name in names},
            }
        }
    )
    with pytest.raises(ModelError) as error:
        SymbolProvider(model, select_shapes(model), package="pkg")
    for name in names:
        assert f"example#Container${name}" in str(error.value)
    result = "CLASS" if kind in ("enum", "intEnum") else "class_"
    if names[0] == "class":
        assert repr(result) in str(error.value)


def test_declaration_collisions_after_rename() -> None:
    from smithy_python.model import ModelError, ServiceShape
    from smithy_python.selection import Selection

    model = model_with(
        {
            "example#Service": {
                "type": "service",
                "rename": {"example#Second": "HTTPServer"},
            },
            "example#Http_Server": {"type": "structure"},
            "example#Second": {"type": "enum"},
        }
    )
    selection = Selection(
        model.expect_shape("example#Service", ServiceShape),
        (model.get_shape("example#Http_Server"), model.get_shape("example#Second")),
        0,
    )
    with pytest.raises(ModelError) as error:
        SymbolProvider(model, selection, package="pkg")
    assert "'HttpServer'" in str(error.value)
    assert "example#Http_Server" in str(error.value)
    assert "example#Second" in str(error.value)


def test_only_emitted_declarations_collide() -> None:
    from smithy_python.symbols import TypeReference

    model = model_with(
        {
            "example#HTTPServer": {"type": "string"},
            "example#Http_Server": {"type": "structure"},
            "example#Document": {
                "type": "structure",
                "members": {
                    "list": {"target": "smithy.api#Document"},
                    "dict": {"target": "smithy.api#String"},
                },
            },
            "example#List": {"type": "enum"},
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    assert symbols.type_reference("example#Document") == TypeReference(
        "Document", "pkg.models"
    )
    assert symbols.type_reference("smithy.api#Document") == TypeReference(
        "Document", "smithy_core.documents"
    )
    assert symbols.member_name("example#Document$list") == "list"
    assert symbols.member_name("example#Document$dict") == "dict"


@pytest.mark.parametrize(
    "package",
    [
        "",
        ".pkg",
        "pkg.",
        "pkg..models",
        "1pkg",
        "pkg-name",
        "pkg.class",
        "None",
        "pkg/child",
        "pkg.\uff43\uff4c\uff41\uff53\uff53",
    ],
)
def test_invalid_package(package: str) -> None:
    model = model_with({})
    with pytest.raises(ValueError, match="Python package"):
        SymbolProvider(model, select_shapes(model), package=package)


@pytest.mark.parametrize(
    "name,expected",
    [("2HTTPServer", "_2HttpServer"), ("__init__", "Init"), ("None", "None_")],
)
def test_rename_normalization(name: str, expected: str) -> None:
    from smithy_python.model import ServiceShape
    from smithy_python.selection import Selection

    model = model_with(
        {
            "example#Service": {"type": "service", "rename": {"example#Data": name}},
            "example#Data": {"type": "structure"},
        }
    )
    selection = Selection(
        model.expect_shape("example#Service", ServiceShape),
        (model.get_shape("example#Data"),),
        0,
    )
    assert (
        SymbolProvider(model, selection, package="pkg").declaration_name("example#Data")
        == expected
    )


@pytest.mark.parametrize("kind", ["blob", "union"])
def test_streaming_rejected_when_resolved(kind: str) -> None:
    from smithy_python.model import ModelError

    model = model_with(
        {
            "example#Stream": {"type": kind, "traits": {"smithy.api#streaming": {}}},
            "example#Streams": {"type": "list", "member": {"target": "example#Stream"}},
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    for shape_id in ("example#Stream", "example#Streams"):
        with pytest.raises(ModelError, match=r"Unsupported streaming.*example#Stream"):
            symbols.type_reference(shape_id)
    with pytest.raises(ModelError, match="Unsupported streaming"):
        symbols.declaration_name("example#Stream")


def test_request_boundaries() -> None:
    from smithy_python.model import InvalidShapeIdError, ModelError, ShapeNotFoundError
    from smithy_python.selection import Selection

    model = model_with(
        {
            "example#Data": {
                "type": "structure",
                "members": {"value": {"target": "smithy.api#String"}},
            },
            "example#Excluded": {"type": "structure"},
            "example#Alias": {"type": "string"},
            "example#Items": {"type": "list", "member": {"target": "example#Excluded"}},
            "example#Service": {"type": "service"},
            "example#Operation": {"type": "operation"},
            "example#Resource": {"type": "resource"},
            "example#Trait": {"type": "structure", "traits": {"smithy.api#trait": {}}},
            "example#Mixin": {"type": "structure", "traits": {"smithy.api#mixin": {}}},
        }
    )
    selection = Selection(
        None,
        tuple(
            model.get_shape(f"example#{name}") for name in ("Data", "Alias", "Items")
        ),
        1,
    )
    symbols = SymbolProvider(model, selection, package="pkg")
    for method in (
        symbols.type_reference,
        symbols.declaration_name,
        symbols.member_name,
    ):
        with pytest.raises(InvalidShapeIdError):
            method("Data")
        with pytest.raises(ShapeNotFoundError):
            method("example#Missing")
        with pytest.raises(ModelError, match="not selected"):
            method("example#Excluded")
    for name in ("Service", "Operation", "Resource", "Trait", "Mixin"):
        with pytest.raises(ModelError):
            symbols.type_reference(f"example#{name}")
    for shape_id in ("example#Alias", "example#Items", "smithy.api#Unit"):
        with pytest.raises(ModelError, match="No generated declaration"):
            symbols.declaration_name(shape_id)
    with pytest.raises(ModelError, match="member ID"):
        symbols.type_reference("example#Data$value")
    with pytest.raises(ModelError, match="member ID"):
        symbols.member_name("example#Data")
    with pytest.raises(ModelError, match="not selected"):
        symbols.type_reference("example#Items")


@pytest.mark.parametrize("rename", ["___", "bad-name", "", "has space"])
def test_invalid_rename_has_original_id(rename: str) -> None:
    from smithy_python.model import ModelError, ServiceShape
    from smithy_python.selection import Selection

    model = model_with(
        {
            "example#Service": {"type": "service", "rename": {"example#Data": rename}},
            "example#Data": {"type": "structure"},
        }
    )
    selection = Selection(
        model.expect_shape("example#Service", ServiceShape),
        (model.get_shape("example#Data"),),
        0,
    )
    with pytest.raises(ModelError, match="example#Data"):
        SymbolProvider(model, selection, package="pkg")


def test_deep_collection_cycle_is_not_python_recursion() -> None:
    from smithy_python.model import ModelError

    shapes: dict[str, object] = {
        f"example#List{i}": {
            "type": "list",
            "member": {"target": f"example#List{(i + 1) % 1100}"},
        }
        for i in range(1100)
    }
    model = model_with(shapes)
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    with pytest.raises(ModelError, match="Collection-only cycle"):
        symbols.type_reference("example#List0")


def test_package_is_keyword_only() -> None:
    model = model_with({})
    with pytest.raises(TypeError):
        SymbolProvider(model, select_shapes(model), "pkg")  # type: ignore


@pytest.mark.parametrize("members", [False, True])
def test_collision_diagnostics_follow_model_order(members: bool) -> None:
    from smithy_python.model import ModelError

    first, second = (
        ("example#Data$get_url", "example#Data$getURL")
        if members
        else ("z#Get_Url", "a#GetUrl")
    )
    shapes: dict[str, object] = (
        {
            "example#Data": {
                "type": "structure",
                "members": {
                    "get_url": {"target": "smithy.api#String"},
                    "getURL": {"target": "smithy.api#String"},
                },
            }
        }
        if members
        else {first: {"type": "structure"}, second: {"type": "structure"}}
    )
    model = model_with(shapes)
    with pytest.raises(ModelError) as error:
        SymbolProvider(model, select_shapes(model), package="pkg")
    message = str(error.value)
    assert message.index(first) < message.index(second)


def test_cycle_diagnostic_excludes_noncyclic_prefix() -> None:
    from smithy_python.model import ModelError

    model = model_with(
        {
            "example#Prefix": {"type": "list", "member": {"target": "example#Loop"}},
            "example#Loop": {"type": "list", "member": {"target": "example#Other"}},
            "example#Other": {"type": "list", "member": {"target": "example#Loop"}},
        }
    )
    symbols = SymbolProvider(model, select_shapes(model), package="pkg")
    with pytest.raises(ModelError) as error:
        symbols.type_reference("example#Prefix")
    assert str(error.value) == (
        "Collection-only cycle: example#Loop -> example#Other -> example#Loop"
    )
