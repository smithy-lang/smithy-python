#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from types import MappingProxyType, ModuleType
from typing import Any

import pytest
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._schema_compact import StaticSchema, hydrate
from smithy_core.documents import Document
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType

NS = "ns.example"
STRING = ShapeType.STRING.value
INTEGER = ShapeType.INTEGER.value
DOCUMENT = ShapeType.DOCUMENT.value

# Valueless member traits are bits (see _schema_compact._TRAIT_BITS).
REQUIRED = 1
IDEMPOTENCY_TOKEN = 1 << 1
SPARSE = 1 << 6
INPUT = {"smithy.api#input": None}
STREAMING = {"smithy.api#streaming": None}


def _shape(
    shape_type: ShapeType,
    name: str,
    members: tuple[tuple[str, object, Any], ...] = (),
    traits: Any = 0,
) -> StaticSchema:
    return (
        shape_type.value,
        NS,
        name,
        traits,
        tuple(m[0] for m in members),
        tuple((m[1], m[2]) for m in members),
    )


def _struct(name: str, *members: tuple[str, object, Any], traits: Any = 0):
    return _shape(ShapeType.STRUCTURE, name, members, traits)


def _union(name: str, *members: tuple[str, object, Any], traits: Any = 0):
    return _shape(ShapeType.UNION, name, members, traits)


def _list(name: str, member: object, traits: Any = 0) -> StaticSchema:
    return _shape(ShapeType.LIST, name, (("member", member, 0),), traits)


def _map(name: str, value: object, traits: Any = 0) -> StaticSchema:
    return _shape(
        ShapeType.MAP, name, (("key", STRING, 0), ("value", value, 0)), traits
    )


def _registry(**consts: StaticSchema) -> tuple[ModelRegistry, ModuleType]:
    """Build a registry over the given schema constants, plus their models module."""
    mod = ModuleType("ns.example._private.schemas")
    for const, tup in consts.items():
        setattr(mod, const, tup)
    return ModelRegistry(mod), mod


# A small model in the shape of STS AssumeRole plus a union, a document, a sparse
# list, and a map, used by most tests below.
TAG = _struct("Tag", ("Key", STRING, REQUIRED), ("Value", STRING, REQUIRED))
POLICY = _struct("PolicyDescriptorType", ("arn", STRING, 0))
CONTENT = _union(
    "ContentBlock",
    ("text", STRING, 0),
    ("image", lambda: IMAGE, 0),
    ("bytes", ShapeType.BLOB.value, 0),
)
IMAGE = _struct("ImageBlock", ("format", STRING, REQUIRED), ("Source", STRING, 0))
TAGS = _list("TagList", TAG)
POLICIES = _list("PolicyList", POLICY)
CONTENTS = _list("ContentList", CONTENT)
NAMES = _list("NameList", STRING)
SPARSE_NAMES = _list("SparseNameList", STRING, SPARSE)
TAG_MAP = _map("TagMap", TAG)
NAME_MAP = _map("NameMap", STRING)
EVENTS = _union("Events", ("ping", STRING, 0), traits=STREAMING)
INPUT_SCHEMA = _struct(
    "AssumeRoleInput",
    ("RoleArn", STRING, REQUIRED),
    ("RoleSessionName", STRING, REQUIRED),
    ("PolicyArns", POLICIES, 0),
    ("Tags", TAGS, 0),
    ("TagMap", TAG_MAP, 0),
    ("Names", NAMES, 0),
    ("SparseNames", SPARSE_NAMES, 0),
    ("NameMap", NAME_MAP, 0),
    ("Content", CONTENT, 0),
    ("Contents", CONTENTS, 0),
    ("Doc", DOCUMENT, 0),
    (
        "DurationSeconds",
        INTEGER,
        {"smithy.api#required": None, "smithy.api#default": 3600},
    ),
    ("ClientToken", STRING, REQUIRED | IDEMPOTENCY_TOKEN),
    ("Self", STRING, 0),
    ("Plugins", STRING, 0),
    ("Stream", EVENTS, REQUIRED),
    traits=INPUT,
)
OUTPUT_SCHEMA = _struct(
    "AssumeRoleOutput",
    ("Tags", TAGS, 0),
    ("Content", CONTENT, 0),
    traits={"smithy.api#output": None},
)

REGISTRY, SCHEMAS = _registry(
    TAG=TAG,
    POLICY_DESCRIPTOR_TYPE=POLICY,
    CONTENT_BLOCK=CONTENT,
    IMAGE_BLOCK=IMAGE,
    TAG_LIST=TAGS,
    POLICY_LIST=POLICIES,
    CONTENT_LIST=CONTENTS,
    NAME_LIST=NAMES,
    SPARSE_NAME_LIST=SPARSE_NAMES,
    TAG_MAP=TAG_MAP,
    NAME_MAP=NAME_MAP,
    EVENTS=EVENTS,
    ASSUME_ROLE_INPUT=INPUT_SCHEMA,
    ASSUME_ROLE_OUTPUT=OUTPUT_SCHEMA,
)
REQUIRED_ARGS = {"role_arn": "arn", "role_session_name": "session"}


def _input(**params: Any) -> Any:
    return REGISTRY.input_from_params(hydrate(INPUT_SCHEMA), params)


def _model(name: str) -> Any:
    return REGISTRY.build(name)


def _invalid(match: str, **params: Any) -> None:
    with pytest.raises(TypeError, match=match):
        _input(**params)


def test_input_fields_escape_self_and_plugins() -> None:
    fields = _model("AssumeRoleInput").__dataclass_fields__
    assert {"self_", "plugins_"} <= set(fields)
    result = _input(**REQUIRED_ARGS, self_="s", plugins_="p")
    assert (result.self_, result.plugins_) == ("s", "p")


def test_builds_input_from_keyword_arguments() -> None:
    result = _input(**REQUIRED_ARGS, names=["a"])
    assert type(result) is _model("AssumeRoleInput")
    assert (result.role_arn, result.role_session_name) == ("arn", "session")
    assert result.names == ["a"]


def test_ignores_operation_method_arguments() -> None:
    result = _input(**REQUIRED_ARGS, self=object(), plugins=[])
    assert result.role_arn == "arn"


def test_none_is_unset() -> None:
    result = _input(**REQUIRED_ARGS, names=None, duration_seconds=None)
    assert result.names is None
    assert result.duration_seconds == 3600  # the model default applies


def test_nested_dicts_and_models_mix() -> None:
    policy = _model("PolicyDescriptorType")
    result = _input(
        **REQUIRED_ARGS,
        policy_arns=[{"arn": "a"}, policy(arn="b")],
        tags=({"key": "k", "value": "v"},),
        tag_map={"x": {"key": "k", "value": "v"}},
    )
    assert result.policy_arns == [policy(arn="a"), policy(arn="b")]
    assert result.tags == [_model("Tag")(key="k", value="v")]
    assert result.tag_map == {"x": _model("Tag")(key="k", value="v")}


def test_models_pass_through_unchanged() -> None:
    policies = [_model("PolicyDescriptorType")(arn="a")]
    tag = _model("Tag")(key="k", value="v")
    result = _input(**REQUIRED_ARGS, policy_arns=policies, tag_map={"x": tag})
    assert result.policy_arns[0] is policies[0]
    assert result.tag_map["x"] is tag


def test_scalar_collections_are_not_copied() -> None:
    names = ["a", "b"]
    name_map = {"a": "b"}
    result = _input(**REQUIRED_ARGS, names=names, name_map=name_map)
    assert result.names is names
    assert result.name_map is name_map


def test_sparse_list_keeps_none() -> None:
    assert _input(**REQUIRED_ARGS, sparse_names=["a", None]).sparse_names == [
        "a",
        None,
    ]


def test_union_dicts_build_variants() -> None:
    text = _input(**REQUIRED_ARGS, content={"text": "hi"}).content
    assert text == _model("ContentBlockText")(value="hi")
    image = _input(**REQUIRED_ARGS, content={"image": {"format": "png"}}).content
    assert image == _model("ContentBlockImage")(
        value=_model("ImageBlock")(format="png")
    )
    blob = _input(**REQUIRED_ARGS, content={"bytes_": b"x"}).content
    assert blob == _model("ContentBlockBytes")(value=b"x")


def test_union_dict_ignores_none_members() -> None:
    result = _input(**REQUIRED_ARGS, content={"text": "hi", "image": None})
    assert result.content == _model("ContentBlockText")(value="hi")


def test_union_variant_passes_through() -> None:
    variant = _model("ContentBlockText")(value="hi")
    assert _input(**REQUIRED_ARGS, contents=[variant]).contents[0] is variant


def test_document_values_are_wrapped() -> None:
    assert _input(**REQUIRED_ARGS, doc={"a": [1]}).doc == Document({"a": [1]})
    document = Document("x")
    assert _input(**REQUIRED_ARGS, doc=document).doc is document


def test_event_stream_member_is_not_a_parameter() -> None:
    # The stream member is @required, but events go through the returned stream.
    assert "stream" not in _model("AssumeRoleInput").__dataclass_fields__
    assert "stream" not in _input(**REQUIRED_ARGS).to_dict()
    _invalid(r"Unknown parameter stream for AssumeRoleInput", **REQUIRED_ARGS, stream=1)


def test_idempotency_token_and_default_members_may_be_omitted() -> None:
    result = _input(**REQUIRED_ARGS)
    assert result.client_token is None
    assert result.duration_seconds == 3600


def test_idempotency_token_is_required_outside_operation_input() -> None:
    nested = _struct("Nested", ("Token", STRING, REQUIRED | IDEMPOTENCY_TOKEN))
    outer = _struct("Outer", ("Nested", nested, 0), traits=INPUT)
    registry, _ = _registry(NESTED=nested, OUTER=outer)
    with pytest.raises(TypeError, match=r"^Missing required parameter: nested.token$"):
        registry.input_from_params(hydrate(outer), {"nested": {}})


def test_missing_required_members() -> None:
    _invalid(r"^Missing required parameter: role_session_name$", role_arn="a")
    _invalid(
        r"^Missing required parameters: role_arn, role_session_name$",
        role_arn=None,
        role_session_name=None,
    )
    _invalid(
        r"^Missing required parameter: tags\[1\]\.value$",
        **REQUIRED_ARGS,
        tags=[{"key": "k", "value": "v"}, {"key": "k", "value": None}],
    )
    _invalid(
        r"^Missing required parameters: tag_map\['x'\]\.key, tag_map\['x'\]\.value$",
        **REQUIRED_ARGS,
        tag_map={"x": {}},
    )
    _invalid(
        r"^Missing required parameter: contents\[0\]\.image\.format$",
        **REQUIRED_ARGS,
        contents=[{"image": {}}],
    )


def test_unknown_keys() -> None:
    _invalid(
        r"^Unknown parameter policy_arns\[0\]\.arnn for PolicyDescriptorType; "
        r"did you mean 'arn'\?$",
        **REQUIRED_ARGS,
        policy_arns=[{"arnn": "a"}],
    )
    # An unknown key is rejected even when its value is None.
    _invalid(
        r"^Unknown parameter policy_arns\[0\]\.zzz for PolicyDescriptorType$",
        **REQUIRED_ARGS,
        policy_arns=[{"zzz": None}],
    )
    # Dict keys are Python member names, escaped like model attributes.
    _invalid(
        r"^Unknown parameter content\.bytes for union ContentBlock; "
        r"did you mean 'bytes_'\?$",
        **REQUIRED_ARGS,
        content={"bytes": b"x"},
    )
    _invalid(
        r"^Unknown parameter content\.zzz for union ContentBlock$",
        **REQUIRED_ARGS,
        content={"text": "a", "zzz": None},
    )


def test_union_dict_must_set_exactly_one_member() -> None:
    _invalid(
        r"^Invalid parameter content: a ContentBlock dict must set exactly one "
        r"member, got 0$",
        **REQUIRED_ARGS,
        content={},
    )
    _invalid(r"got 0$", **REQUIRED_ARGS, content={"text": None})
    _invalid(
        r"^Invalid parameter contents\[1\]: a ContentBlock dict must set exactly one "
        r"member, got 2 \(image, text\)$",
        **REQUIRED_ARGS,
        contents=[{"text": "a"}, {"text": "a", "image": {"format": "png"}}],
    )


@pytest.mark.parametrize("value", ["abc", b"abc", bytearray(b"abc")])
def test_str_bytes_and_bytearray_are_not_lists(value: object) -> None:
    _invalid(
        rf"^Invalid parameter names: expected a sequence for a list member, got "
        rf"{type(value).__name__}$",
        **REQUIRED_ARGS,
        names=value,
    )


def test_errors_are_plain_type_errors_without_internal_context() -> None:
    with pytest.raises(TypeError) as info:
        _input(role_arn="a")
    assert type(info.value) is TypeError
    assert info.value.__cause__ is None
    assert info.value.__suppress_context__


def test_recursive_shapes() -> None:
    node = _struct("Node", ("Value", STRING, 0), ("Next", lambda: node, 0), traits=0)
    root = _struct("Root", ("Node", node, 0), traits=INPUT)
    registry, _ = _registry(NODE=node, ROOT=root)
    result = registry.input_from_params(
        hydrate(root), {"node": {"value": "a", "next": {"value": "b"}}}
    )
    assert result.node.next.value == "b"
    with pytest.raises(TypeError, match=r"^Unknown parameter node\.next\.next\.x "):
        registry.input_from_params(
            hydrate(root), {"node": {"next": {"next": {"x": 1}}}}
        )


def test_renamed_structure_builds_its_own_class() -> None:
    # Two shapes share the id name "Greeting"; codegen renames one and records it.
    greeting = _struct("Greeting", ("hi", STRING, 0))
    other = (
        ShapeType.STRUCTURE.value,
        "other.ns",
        "Greeting",
        0,
        ("salutation",),
        ((STRING, 0),),
    )
    root = _struct("Root", ("A", greeting, 0), ("B", other, 0), traits=INPUT)
    mod = ModuleType("ns.example._private.schemas")
    for const, tup in {"GREETING": greeting, "RENAMED": other, "ROOT": root}.items():
        setattr(mod, const, tup)
    registry = ModelRegistry(mod, renames={"RenamedGreeting": "RENAMED"})
    result = registry.input_from_params(
        hydrate(root), {"a": {"hi": "x"}, "b": {"salutation": "y"}}
    )
    assert type(result.a).__name__ == "Greeting"
    assert type(result.b).__name__ == "RenamedGreeting"


def test_to_dict() -> None:
    result = _input(
        **REQUIRED_ARGS,
        tags=[{"key": "k", "value": "v"}],
        tag_map={"x": {"key": "k", "value": "v"}},
        content={"image": {"format": "png"}},
        contents=[{"text": "a"}, {"bytes_": b"b"}],
        sparse_names=["a", None],
        doc={"a": [1]},
    )
    assert result.to_dict() == {
        **REQUIRED_ARGS,
        "tags": [{"key": "k", "value": "v"}],
        "tag_map": {"x": {"key": "k", "value": "v"}},
        "content": {"image": {"format": "png"}},
        "contents": [{"text": "a"}, {"bytes_": b"b"}],
        "sparse_names": ["a", None],
        "doc": {"a": [1]},
        "duration_seconds": 3600,
    }


def test_to_dict_round_trips() -> None:
    result = _input(
        **REQUIRED_ARGS,
        policy_arns=[{"arn": "a"}],
        tag_map={"x": {"key": "k", "value": "v"}},
        contents=[{"image": {"format": "png", "source": "s"}}],
        doc=[1, {"b": None}],
    )
    assert _input(**result.to_dict()) == result


def test_to_dict_returns_new_containers() -> None:
    names = ["a"]
    name_map = {"a": "b"}
    result = _input(**REQUIRED_ARGS, names=names, name_map=name_map).to_dict()
    assert result["names"] == names and result["names"] is not names
    assert result["name_map"] == name_map and result["name_map"] is not name_map


def test_to_dict_on_outputs_and_variants() -> None:
    output = _model("AssumeRoleOutput")(content=_model("ContentBlockText")(value="a"))
    # response_metadata is not a member, so it is left out.
    assert output.to_dict() == {"content": {"text": "a"}}
    assert _model("ContentBlockBytes")(value=b"x").to_dict() == {"bytes_": b"x"}
    # An unknown variant has no dictionary form.
    assert _model("ContentBlockUnknown")(tag="x").to_dict() == {}


def test_params_names_are_dict_at_runtime() -> None:
    assert _model("TagParams") is dict
    assert _model("ContentBlockParams") is dict
    assert _model("ContentBlockTextParams") is dict
    assert _model("AssumeRoleInputParams") is dict
    for name in ["ContentBlockUnknownParams", "NopeParams", "Tag_Params", "Params"]:
        with pytest.raises(AttributeError):
            _model(name)


def test_params_name_collision_uses_underscore() -> None:
    # A real shape named FooParams takes the name, so Foo's form is Foo_Params.
    foo = _struct("Foo", ("a", STRING, 0))
    foo_params = _struct("FooParams", ("b", STRING, 0))
    enum = (ShapeType.ENUM.value, NS, "Color", 0, ("RED",), ((-1, 0),))
    registry, _ = _registry(FOO=foo, FOO_PARAMS=foo_params, COLOR=enum)
    assert registry.build("Foo_Params") is dict
    assert registry.build("FooParams").__name__ == "FooParams"
    assert registry.build("FooParamsParams") is dict
    with pytest.raises(AttributeError):
        registry.build("ColorParams")
    assert registry.build("UnitParams") is dict


def test_operation_builds_input_through_registry() -> None:
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            NS,
            "AssumeRole",
            0,
            INPUT_SCHEMA,
            OUTPUT_SCHEMA,
            (),
        ),
        model_registry=REGISTRY,
    )
    result = operation.input_from_params({**REQUIRED_ARGS, "plugins": None})
    assert result == _input(**REQUIRED_ARGS)


def test_other_sequences_and_mappings_become_lists_and_dicts() -> None:
    result = _input(
        **REQUIRED_ARGS,
        names=("a", "b"),
        name_map=MappingProxyType({"a": "b"}),
        tag_map=MappingProxyType({"x": MappingProxyType({"key": "k", "value": "v"})}),
        content=MappingProxyType({"text": "hi"}),
    )
    assert result.names == ["a", "b"]
    name_map: Any = result.name_map
    assert type(name_map) is dict and name_map == {"a": "b"}
    assert result.tag_map == {"x": _model("Tag")(key="k", value="v")}
    assert result.content == _model("ContentBlockText")(value="hi")


def test_unknown_key_hints_match_case_and_escaping() -> None:
    _invalid(
        r"^Unknown parameter policy_arns\[0\]\.Arn for PolicyDescriptorType; "
        r"did you mean 'arn'\?$",
        **REQUIRED_ARGS,
        policy_arns=[{"Arn": "a"}],
    )
    _invalid(r"did you mean 'bytes_'\?$", **REQUIRED_ARGS, content={"BYTES": b"x"})
    _invalid(r"did you mean 'text'\?$", **REQUIRED_ARGS, content={"Text": "x"})


def test_non_str_keys_are_unknown() -> None:
    _invalid(
        r"^Unknown parameter key 1 in policy_arns\[0\] for PolicyDescriptorType$",
        **REQUIRED_ARGS,
        policy_arns=[{1: "a"}],
    )
    _invalid(
        r"^Unknown parameter key \(1, 2\) in content for union ContentBlock$",
        **REQUIRED_ARGS,
        content={(1, 2): "a", "text": "b"},
    )


def test_null_document_round_trips() -> None:
    # None means unset, so a JSON null document stays a Document in dict form.
    result = _input(**REQUIRED_ARGS, doc=Document(None))
    assert result.to_dict()["doc"] == Document(None)
    assert _input(**result.to_dict()) == result


def test_to_dict_copies_document_values() -> None:
    raw = {"a": [1, {"b": 2}]}
    result = _input(**REQUIRED_ARGS, doc=raw)
    as_dict = result.to_dict()
    assert as_dict["doc"] == raw
    as_dict["doc"]["a"][1]["b"] = 3
    assert raw["a"][1]["b"] == 2  # type: ignore[index]
    assert result.doc == Document({"a": [1, {"b": 2}]})


def test_to_dict_on_errors() -> None:
    error = _struct(
        "Boom",
        ("message", STRING, 0),
        ("Code", STRING, 0),
        traits={"smithy.api#error": "client"},
    )
    registry, _ = _registry(BOOM=error)
    assert registry.build("Boom")(message="m", code="c").to_dict() == {
        "message": "m",
        "code": "c",
    }


def test_variant_params_name_collision() -> None:
    # Union Choice has a member named params, whose variant class is ChoiceParams;
    # the union's own form is then Choice_Params.
    choice = _union("Choice", ("params", STRING, 0), ("other", STRING, 0))
    registry, _ = _registry(CHOICE=choice)
    registry.build("Choice")
    assert registry.params_name("Choice") == "Choice_Params"
    assert registry.build("Choice_Params") is dict
    assert registry.build("ChoiceParamsParams") is dict
    assert registry.build("ChoiceParams").__name__ == "ChoiceParams"


def test_params_name_of_name_ending_in_underscore() -> None:
    # Reserved class names are escaped with a trailing underscore (e.g. None_).
    escaped = _struct("None_", ("a", STRING, 0))
    registry, _ = _registry(NONE_=escaped)
    assert registry.params_name("None_") == "None_Params"
    assert registry.build("None_Params") is dict
