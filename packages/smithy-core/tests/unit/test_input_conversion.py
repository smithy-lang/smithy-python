#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
"""Keyword operation inputs: building input models from keyword arguments."""

from types import ModuleType
from typing import Any

import pytest
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._schema_compact import StaticSchema, hydrate
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType

NS = "ns.example"

STRING = ShapeType.STRING.value
INTEGER = ShapeType.INTEGER.value

REQUIRED = 1 << 0
IDEMPOTENCY_TOKEN = 1 << 1
SENSITIVE = 1 << 2
SPARSE = 1 << 6

_INPUT = "smithy.api#input"
_DEFAULT = "smithy.api#default"
_REQUIRED = "smithy.api#required"

type _Member = tuple[str, object] | tuple[str, object, object]


def _collection(
    shape_type: ShapeType, name: str, members: tuple[_Member, ...], traits: object = 0
) -> StaticSchema:
    return (
        shape_type.value,
        NS,
        name,
        traits,
        tuple(m[0] for m in members),
        tuple((m[1], m[2] if len(m) > 2 else 0) for m in members),
    )


def _struct(name: str, *members: _Member, traits: object = 0) -> StaticSchema:
    return _collection(ShapeType.STRUCTURE, name, members, traits)


def _input(name: str, *members: _Member) -> StaticSchema:
    return _collection(ShapeType.STRUCTURE, name, members, {_INPUT: None})


def _registry(**consts: StaticSchema) -> ModelRegistry:
    module = ModuleType(f"{NS}._private.schemas")
    for const, schema in consts.items():
        setattr(module, const, schema)
    return ModelRegistry(module)


EMPTY_INPUT = _input("EmptyInput")

ASSUME_ROLE_INPUT = _input(
    "AssumeRoleInput",
    ("RoleArn", STRING, REQUIRED),
    ("RoleSessionName", STRING, REQUIRED),
    ("DurationSeconds", INTEGER),
    ("ExternalId", STRING),
)

DEFAULTS_INPUT = _input(
    "DefaultsInput",
    ("Name", STRING, REQUIRED),
    ("PageSize", INTEGER, {_REQUIRED: None, _DEFAULT: 25}),
    ("ClientToken", STRING, REQUIRED | IDEMPOTENCY_TOKEN),
)


def _build(schema: StaticSchema, registry: ModelRegistry, **members: Any) -> Any:
    return registry.build_input(hydrate(schema), members, "Operation")


def _schema(schema: StaticSchema) -> Schema:
    return hydrate(schema)


def test_keyword_members_build_the_input_model() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    built = _build(
        ASSUME_ROLE_INPUT,
        registry,
        role_arn="arn:aws:iam::123456789012:role/my-role",
        role_session_name="my-session",
        duration_seconds=900,
    )

    assert type(built) is registry.build("AssumeRoleInput")
    assert built.role_arn == "arn:aws:iam::123456789012:role/my-role"
    assert built.role_session_name == "my-session"
    assert built.duration_seconds == 900
    assert built.external_id is None


def test_operation_without_members_builds_an_empty_input() -> None:
    registry = _registry(EMPTY_INPUT=EMPTY_INPUT)

    built = _build(EMPTY_INPUT, registry)

    assert type(built) is registry.build("EmptyInput")


def test_none_is_the_same_as_omitting_an_optional_member() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    explicit = _build(
        ASSUME_ROLE_INPUT,
        registry,
        role_arn="arn",
        role_session_name="session",
        duration_seconds=None,
        external_id=None,
    )
    omitted = _build(
        ASSUME_ROLE_INPUT, registry, role_arn="arn", role_session_name="session"
    )

    assert explicit == omitted


def test_unknown_member_raises_type_error() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    with pytest.raises(TypeError, match=r"Operation.*unknown member 'role_name'"):
        _build(
            ASSUME_ROLE_INPUT,
            registry,
            role_arn="arn",
            role_session_name="session",
            role_name="x",
        )


def test_unknown_member_in_wire_casing_suggests_the_python_name() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    with pytest.raises(TypeError, match=r"'RoleArn' \(did you mean 'role_arn'\?\)"):
        registry.build_input(
            _schema(ASSUME_ROLE_INPUT),
            {"RoleArn": "arn", "role_session_name": "session"},
            "Operation",
        )


def test_missing_required_members_are_all_named() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    with pytest.raises(TypeError) as error:
        _build(ASSUME_ROLE_INPUT, registry, duration_seconds=900)

    message = str(error.value)
    assert "missing required members 'role_arn', 'role_session_name'" in message


def test_none_for_a_required_member_counts_as_missing() -> None:
    registry = _registry(ASSUME_ROLE_INPUT=ASSUME_ROLE_INPUT)

    with pytest.raises(TypeError, match=r"missing required member 'role_arn'"):
        _build(ASSUME_ROLE_INPUT, registry, role_arn=None, role_session_name="session")


def test_required_member_with_a_default_may_be_omitted() -> None:
    registry = _registry(DEFAULTS_INPUT=DEFAULTS_INPUT)

    built = _build(DEFAULTS_INPUT, registry, name="n")

    assert built.name == "n"
    assert built.page_size == 25


@pytest.mark.parametrize(
    "members", [{}, {"client_token": None}], ids=["omitted", "none"]
)
def test_unset_idempotency_token_is_left_unset(members: dict[str, Any]) -> None:
    registry = _registry(DEFAULTS_INPUT=DEFAULTS_INPUT)
    given = {"name": "n", **members}

    built = registry.build_input(hydrate(DEFAULTS_INPUT), given, "Operation")

    # ClientToken is required, yet an operation's own token may be omitted. The
    # pipeline generates it once the interceptors have run, so building the input
    # neither demands the token nor fills it.
    assert built.client_token is None
    assert given == {"name": "n", **members}


@pytest.mark.parametrize("token", ["", "caller-token"])
def test_given_idempotency_token_is_kept(token: str) -> None:
    registry = _registry(DEFAULTS_INPUT=DEFAULTS_INPUT)

    built = _build(DEFAULTS_INPUT, registry, name="n", client_token=token)

    assert built.client_token == token


def test_none_for_a_defaulted_member_applies_the_default() -> None:
    registry = _registry(DEFAULTS_INPUT=DEFAULTS_INPUT)

    built = _build(DEFAULTS_INPUT, registry, name="n", page_size=None)

    assert built.page_size == 25


def _list(name: str, target: object, traits: object = 0) -> StaticSchema:
    return _collection(ShapeType.LIST, name, (("member", target),), traits)


def _map(name: str, target: object, traits: object = 0) -> StaticSchema:
    return _collection(
        ShapeType.MAP, name, (("key", STRING), ("value", target)), traits
    )


def _union(name: str, *members: _Member) -> StaticSchema:
    return _collection(ShapeType.UNION, name, members)


TAG = _struct("Tag", ("Key", STRING, REQUIRED), ("Value", STRING, REQUIRED))
POLICY = _struct("Policy", ("Arn", STRING))
OTHER = _struct("Other", ("Arn", STRING))
POLICY_LIST = _list("PolicyList", POLICY)
STRING_LIST = _list("StringList", STRING)
SPARSE_STRING_LIST = _list("SparseStringList", STRING, SPARSE)
TAG_MAP = _map("TagMap", TAG)
STRING_MAP = _map("StringMap", STRING)
SPARSE_STRING_MAP = _map("SparseStringMap", STRING, SPARSE)

# Recursive: a node holds blocks, and a block may hold a node.
BLOCK: StaticSchema = _union(
    "Block",
    ("text", STRING),
    ("tag", TAG),
    ("node", lambda: NODE),
    ("items", STRING_LIST),
)
BLOCK_LIST = _list("BlockList", BLOCK)
NODE: StaticSchema = _struct(
    "Node",
    ("Name", STRING),
    ("Child", lambda: NODE),
    ("Blocks", BLOCK_LIST),
)

NESTED_INPUT = _input(
    "NestedInput",
    ("Policy", POLICY),
    ("PolicyArns", POLICY_LIST),
    ("AccountIds", STRING_LIST),
    ("SparseIds", SPARSE_STRING_LIST),
    ("Tags", TAG_MAP),
    ("Labels", STRING_MAP),
    ("SparseLabels", SPARSE_STRING_MAP),
    ("Content", BLOCK),
    ("Root", NODE),
)
# An output that shares the Policy and Block shapes with the input.
NESTED_OUTPUT = _struct(
    "NestedOutput",
    ("Policy", POLICY),
    ("Content", BLOCK),
    traits={"smithy.api#output": None},
)


def _nested_registry() -> ModelRegistry:
    return _registry(
        TAG=TAG,
        POLICY=POLICY,
        OTHER=OTHER,
        POLICY_LIST=POLICY_LIST,
        STRING_LIST=STRING_LIST,
        SPARSE_STRING_LIST=SPARSE_STRING_LIST,
        TAG_MAP=TAG_MAP,
        STRING_MAP=STRING_MAP,
        SPARSE_STRING_MAP=SPARSE_STRING_MAP,
        BLOCK=BLOCK,
        BLOCK_LIST=BLOCK_LIST,
        NODE=NODE,
        NESTED_INPUT=NESTED_INPUT,
        NESTED_OUTPUT=NESTED_OUTPUT,
    )


def _nested(registry: ModelRegistry, **members: Any) -> Any:
    return registry.build_input(hydrate(NESTED_INPUT), members, "Nested")


def test_nested_dictionary_becomes_the_modeled_structure() -> None:
    registry = _nested_registry()

    built = _nested(registry, policy={"arn": "a"})

    assert built.policy == registry.build("Policy")(arn="a")


def test_list_accepts_dictionaries_models_and_a_mix() -> None:
    registry = _nested_registry()
    policy = registry.build("Policy")
    model = policy(arn="b")

    built = _nested(registry, policy_arns=[{"arn": "a"}, model, {"arn": "c"}])

    assert built.policy_arns == [policy(arn="a"), model, policy(arn="c")]
    assert built.policy_arns[1] is model


def test_tuple_is_accepted_for_a_list_and_stored_as_a_list() -> None:
    registry = _nested_registry()

    built = _nested(registry, account_ids=("1", "2"))

    assert built.account_ids == ["1", "2"]
    assert type(built.account_ids) is list


def test_caller_collections_are_not_mutated_or_shared() -> None:
    registry = _nested_registry()
    policies: list[Any] = [{"arn": "a"}]
    labels = {"k": "v"}

    built = _nested(registry, policy_arns=policies, labels=labels)

    assert policies == [{"arn": "a"}]
    assert built.policy_arns is not policies
    assert built.labels == {"k": "v"}
    assert built.labels is not labels


@pytest.mark.parametrize("value", ["123456789012", b"123", bytearray(b"123")])
def test_string_or_bytes_for_a_list_is_rejected(value: Any) -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=r"at account_ids: expected a list, got"):
        _nested(registry, account_ids=value)


@pytest.mark.parametrize("value", [{"a": 1}, {"a"}, 5, object()])
def test_non_sequence_for_a_list_is_rejected(value: Any) -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=r"at account_ids: expected a list, got"):
        _nested(registry, account_ids=value)


def test_none_is_kept_in_a_sparse_list_and_rejected_in_a_dense_list() -> None:
    registry = _nested_registry()

    built = _nested(registry, sparse_ids=["a", None, "b"])
    assert built.sparse_ids == ["a", None, "b"]

    with pytest.raises(TypeError, match=r"at account_ids\[1\]: None is only allowed"):
        _nested(registry, account_ids=["a", None])


def test_map_values_are_converted() -> None:
    registry = _nested_registry()
    tag = registry.build("Tag")
    model = tag(key="k2", value="v2")

    built = _nested(registry, tags={"a": {"key": "k", "value": "v"}, "b": model})

    assert built.tags == {"a": tag(key="k", value="v"), "b": model}
    assert built.tags["b"] is model


@pytest.mark.parametrize("value", [[("k", "v")], "k=v", 5])
def test_non_mapping_for_a_map_is_rejected(value: Any) -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=r"at labels: expected a dict, got"):
        _nested(registry, labels=value)


def test_non_string_map_key_is_rejected() -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=r"at labels: map keys must be str, got int"):
        _nested(registry, labels={1: "v"})


def test_none_is_kept_in_a_sparse_map_and_rejected_in_a_dense_map() -> None:
    registry = _nested_registry()

    built = _nested(registry, sparse_labels={"a": None, "b": "v"})
    assert built.sparse_labels == {"a": None, "b": "v"}

    with pytest.raises(TypeError, match=r"at labels\['a'\]: None is only allowed"):
        _nested(registry, labels={"a": None})


def test_single_key_dictionary_selects_the_union_variant() -> None:
    registry = _nested_registry()

    built = _nested(registry, content={"text": "Hello"})

    assert built.content == registry.build("BlockText")(value="Hello")


def test_union_variant_value_is_converted() -> None:
    registry = _nested_registry()

    built = _nested(registry, content={"tag": {"key": "k", "value": "v"}})

    assert built.content == registry.build("BlockTag")(
        value=registry.build("Tag")(key="k", value="v")
    )


def test_union_variant_instance_passes_through() -> None:
    registry = _nested_registry()
    variant = registry.build("BlockText")(value="Hello")

    built = _nested(registry, content=variant)

    assert built.content is variant


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({}, r"sets no variant"),
        ({"text": None}, r"the 'text' variant of Block is None"),
        ({"text": "a", "items": ["b"]}, r"exactly one key, got 2: 'text', 'items'"),
        # A key whose value is None is still a key: it is not discarded.
        ({"text": "a", "items": None}, r"exactly one key, got 2: 'text', 'items'"),
        ({"text": "a", "typo": None}, r"exactly one key, got 2: 'text', 'typo'"),
        ({"image": "a"}, r"unknown variant 'image'"),
        ({"image": None}, r"unknown variant 'image'"),
        ("Hello", r"expected a Block variant or a single-key dict, got str"),
        (["text"], r"expected a Block variant or a single-key dict, got list"),
    ],
)
def test_malformed_union_is_rejected(value: Any, message: str) -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=rf"at content: .*{message}"):
        _nested(registry, content=value)


def test_recursive_shapes_convert_at_every_depth() -> None:
    registry = _nested_registry()
    node = registry.build("Node")

    built = _nested(
        registry,
        root={
            "name": "a",
            "child": {"name": "b", "child": {"name": "c"}},
            "blocks": [{"node": {"name": "d", "blocks": [{"text": "e"}]}}],
        },
    )

    assert built.root.child.child == node(name="c")
    inner = built.root.blocks[0]
    assert type(inner) is registry.build("BlockNode")
    assert inner.value.blocks == [registry.build("BlockText")(value="e")]


def test_response_model_is_reused_without_copy_or_mutation() -> None:
    registry = _nested_registry()
    output = registry.build("NestedOutput")(
        policy=registry.build("Policy")(arn="a"),
        content=registry.build("BlockText")(value="t"),
    )
    before = repr(output)

    built = _nested(
        registry,
        policy=output.policy,
        # A response model nested inside a newly written dictionary.
        root={"blocks": [output.content, {"text": "new"}]},
    )

    assert built.policy is output.policy
    assert built.root.blocks[0] is output.content
    assert repr(output) == before


def test_unrelated_model_is_rejected() -> None:
    registry = _nested_registry()
    other = registry.build("Other")(arn="a")

    with pytest.raises(
        TypeError, match=r"at policy: expected Policy or a dict, got Other"
    ):
        _nested(registry, policy=other)
    with pytest.raises(
        TypeError, match=r"at policy_arns\[0\]: expected Policy or a dict, got Other"
    ):
        _nested(registry, policy_arns=[other])
    with pytest.raises(TypeError, match=r"at content: expected a Block variant"):
        _nested(registry, content=other)


def test_whole_input_model_is_not_accepted_for_a_member() -> None:
    registry = _nested_registry()
    whole = registry.build("NestedInput")()

    with pytest.raises(TypeError, match=r"expected Policy or a dict, got NestedInput"):
        _nested(registry, policy=whole)


def test_nested_required_members_are_enforced_in_dictionaries() -> None:
    registry = _nested_registry()

    with pytest.raises(TypeError, match=r"at tags\['a'\]: missing required member"):
        _nested(registry, tags={"a": {"key": "k"}})
    with pytest.raises(TypeError, match=r"at content.tag: missing required members"):
        _nested(registry, content={"tag": {}})


def test_nested_unknown_key_reports_its_path() -> None:
    registry = _nested_registry()

    with pytest.raises(
        TypeError,
        match=r"Invalid Nested input at root.child.blocks\[1\].node: "
        r"unknown member 'nam'",
    ):
        _nested(
            registry,
            root={"child": {"blocks": [{"text": "ok"}, {"node": {"nam": "x"}}]}},
        )


def test_errors_never_include_values() -> None:
    registry = _nested_registry()
    secret = "hunter2-secret-value"
    attempts: list[dict[str, Any]] = [
        {"account_ids": secret},
        {"labels": secret},
        {"policy": secret},
        {"content": secret},
        {"policy": {"arn": "a", "bogus": secret}},
        {"policy_arns": [{"bogus": secret}]},
        {"tags": {"a": {"key": secret}}},
        {"content": {"text": secret, "items": [secret]}},
        {"policy": registry.build("Other")(arn=secret)},
        {"labels": {5: secret}},
    ]

    for members in attempts:
        with pytest.raises(TypeError) as error:
            _nested(registry, **members)
        assert secret not in str(error.value)
        # No chained exception whose message could carry the value either.
        assert error.value.__cause__ is None
        assert error.value.__suppress_context__


def test_sensitive_map_keys_are_not_named_in_paths() -> None:
    secrets = _map("Secrets", TAG, SENSITIVE)
    schema = _input("SecretsInput", ("Secrets", secrets))
    registry = _registry(TAG=TAG, SECRETS=secrets, SECRETS_INPUT=schema)

    with pytest.raises(TypeError) as error:
        registry.build_input(
            hydrate(schema), {"secrets": {"api-key-name": {"key": "k"}}}, "Secrets"
        )

    assert "api-key-name" not in str(error.value)
    assert "at secrets[<key>]: missing required member 'value'" in str(error.value)


VAULT = _struct("Vault", ("Tags", TAG_MAP), ("Content", BLOCK), ("Items", POLICY_LIST))
SECRET_TAGS = _map("SecretTags", TAG_MAP, SENSITIVE)
VAULT_INPUT = _input(
    "VaultInput",
    ("Vault", VAULT, SENSITIVE),
    ("SecretTags", SECRET_TAGS),
    ("Open", VAULT),
)


def _vault_registry() -> ModelRegistry:
    return _registry(
        TAG=TAG,
        POLICY=POLICY,
        POLICY_LIST=POLICY_LIST,
        STRING_LIST=STRING_LIST,
        TAG_MAP=TAG_MAP,
        BLOCK=BLOCK,
        BLOCK_LIST=BLOCK_LIST,
        NODE=NODE,
        VAULT=VAULT,
        SECRET_TAGS=SECRET_TAGS,
        VAULT_INPUT=VAULT_INPUT,
    )


@pytest.mark.parametrize(
    ("members", "message"),
    [
        ({"vault": {"S3CR3T": 1}}, "at vault: unknown member <redacted>"),
        (
            {"vault": {"tags": {"S3CR3T": {"key": "k"}}}},
            "at vault.tags[<key>]: missing required member 'value'",
        ),
        (
            {"vault": {"items": [{"S3CR3T": 1}]}},
            "at vault.items[0]: unknown member <redacted>",
        ),
        (
            {"vault": {"content": {"S3CR3T": 1}}},
            "at vault.content: unknown variant <redacted> for Block",
        ),
        (
            {"vault": {"content": {"text": "a", "S3CR3T": 1}}},
            "exactly one key, got 2: 'text', <redacted>",
        ),
        (
            {"vault": {"content": {"node": {"S3CR3T": 1}}}},
            "at vault.content.node: unknown member <redacted>",
        ),
        (
            {"secret_tags": {"S3CR3T": {"S3CR3T-INNER": {"key": "k"}}}},
            "at secret_tags[<key>][<key>]: missing required member 'value'",
        ),
    ],
)
def test_keys_under_a_sensitive_member_are_redacted_at_every_depth(
    members: dict[str, Any], message: str
) -> None:
    registry = _vault_registry()

    with pytest.raises(TypeError) as error:
        registry.build_input(hydrate(VAULT_INPUT), members, "Vault")

    assert "S3CR3T" not in str(error.value)
    assert message in str(error.value)


def test_keys_inside_a_model_under_a_sensitive_member_are_redacted() -> None:
    registry = _vault_registry()
    vault = registry.build("Vault")(
        tags={"S3CR3T": registry.build("Tag")(key=None, value="v")}
    )

    with pytest.raises(TypeError) as error:
        registry.build_input(hydrate(VAULT_INPUT), {"vault": vault}, "Vault")

    assert "S3CR3T" not in str(error.value)
    assert "at vault.tags[<key>]: missing required member 'key'" in str(error.value)


def test_keys_beside_a_sensitive_member_are_still_named() -> None:
    registry = _vault_registry()

    with pytest.raises(TypeError, match=r"at open: unknown member 'bogus'"):
        registry.build_input(
            hydrate(VAULT_INPUT), {"vault": {}, "open": {"bogus": 1}}, "Vault"
        )
    with pytest.raises(
        TypeError, match=r"at open.tags\['visible'\]: missing required member 'value'"
    ):
        registry.build_input(
            hydrate(VAULT_INPUT),
            {"vault": {}, "open": {"tags": {"visible": {"key": "k"}}}},
            "Vault",
        )


PAGED = _struct("Paged", ("PageSize", INTEGER, {_REQUIRED: None, _DEFAULT: 25}))
PAGED_INPUT = _input("PagedInput", ("Paged", PAGED))


def test_valid_model_is_passed_through_with_its_contents_untouched() -> None:
    registry = _nested_registry()
    tag = registry.build("Tag")(key="k", value="v")
    blocks = [registry.build("BlockTag")(value=tag)]
    node = registry.build("Node")(name="a", blocks=blocks)

    built = _nested(registry, root=node, tags={"a": tag})

    assert built.root is node
    assert node.blocks is blocks
    assert blocks[0].value is tag
    assert built.tags["a"] is tag


def test_model_missing_a_required_member_is_rejected() -> None:
    registry = _nested_registry()
    tag = registry.build("Tag")(key=None, value="v")

    with pytest.raises(
        TypeError, match=r"at tags\['a'\]: missing required member 'key'"
    ):
        _nested(registry, tags={"a": tag})
    with pytest.raises(
        TypeError, match=r"at root.blocks\[0\].tag: missing required member 'key'"
    ):
        _nested(
            registry,
            root=registry.build("Node")(blocks=[registry.build("BlockTag")(value=tag)]),
        )
    assert tag.key is None


def test_dictionary_inside_a_model_is_rejected_and_left_in_place() -> None:
    registry = _nested_registry()
    node = registry.build("Node")
    child = {"bogus": "hunter2"}
    content = [{"text": "hunter2"}]

    with pytest.raises(TypeError) as error:
        _nested(registry, root=node(child=child))
    assert "at root.child: expected Node, got dict" in str(error.value)
    assert "hunter2" not in str(error.value)

    parent = node(blocks=content)
    with pytest.raises(
        TypeError, match=r"at root.blocks\[0\]: expected a Block variant, got dict"
    ):
        _nested(registry, root=parent)
    # The model still holds exactly what the caller put in it.
    assert parent.blocks is content
    assert content == [{"text": "hunter2"}]


def test_unknown_union_variant_model_is_rejected() -> None:
    registry = _nested_registry()
    unknown = registry.build("BlockUnknown")(tag="from-a-newer-service")

    with pytest.raises(TypeError) as error:
        _nested(registry, content=unknown)

    assert "at content: an unknown Block variant cannot be sent" in str(error.value)
    assert "from-a-newer-service" not in str(error.value)
    with pytest.raises(
        TypeError, match=r"at root.blocks\[1\]: an unknown Block variant"
    ):
        _nested(
            registry,
            root=registry.build("Node")(
                blocks=[registry.build("BlockText")(value="a"), unknown]
            ),
        )


@pytest.mark.parametrize(
    ("member", "value", "message"),
    [
        ("content", "BlockText", r"at content: the 'text' variant of Block is None"),
        ("root", "blocks:str", r"at root.blocks: expected a list, got str"),
        ("root", "blocks:None", r"at root.blocks\[0\]: None is only allowed"),
        ("root", "child:Policy", r"at root.child: expected Node, got Policy"),
    ],
)
def test_malformed_model_internals_are_rejected(
    member: str, value: str, message: str
) -> None:
    registry = _nested_registry()
    node = registry.build("Node")
    models: dict[str, Any] = {
        "BlockText": registry.build("BlockText")(value=None),
        "blocks:str": node(blocks="abc"),
        "blocks:None": node(blocks=[None]),
        "child:Policy": node(child=registry.build("Policy")(arn="a")),
    }

    with pytest.raises(TypeError, match=message):
        _nested(registry, **{member: models[value]})


def test_none_for_a_defaulted_member_stays_unset_in_a_model() -> None:
    # A dictionary's None is an omitted member, which takes the modeled default. A
    # model the caller built already made that choice, and is used as it is.
    registry = _registry(PAGED=PAGED, PAGED_INPUT=PAGED_INPUT)
    model = registry.build("Paged")(page_size=None)

    from_model = registry.build_input(hydrate(PAGED_INPUT), {"paged": model}, "Paged")
    from_dict = registry.build_input(
        hydrate(PAGED_INPUT), {"paged": {"page_size": None}}, "Paged"
    )

    assert from_model.paged is model
    assert model.page_size is None
    assert from_dict.paged.page_size == 25


def test_value_that_contains_itself_is_rejected() -> None:
    registry = _nested_registry()
    cyclic: dict[str, Any] = {"name": "a"}
    cyclic["child"] = cyclic
    model = registry.build("Node")(name="a")
    model.child = model

    for root in (cyclic, model):
        with pytest.raises(TypeError) as error:
            _nested(registry, root=root)
        message = str(error.value)
        assert message.startswith("Invalid Nested input at root.child.child.child")
        assert "nested too deeply" in message
        assert len(message) < 300


def test_value_used_in_two_places_is_not_a_cycle() -> None:
    registry = _nested_registry()
    shared: dict[str, Any] = {"name": "shared"}

    built = _nested(
        registry, root={"child": shared, "blocks": [{"node": shared}, {"node": shared}]}
    )

    node = registry.build("Node")(name="shared")
    assert built.root.child == node
    assert [block.value for block in built.root.blocks] == [node, node]


def test_input_members_named_like_method_parameters_are_escaped() -> None:
    schema = _input("CreateInput", ("plugins", STRING_LIST), ("self", STRING))
    nested = _struct("Connector", ("plugins", STRING_LIST), ("self", STRING))
    registry = _registry(STRING_LIST=STRING_LIST, CREATE_INPUT=schema, CONNECTOR=nested)

    built = registry.build_input(
        hydrate(schema), {"plugins_": ["a"], "self_": "me"}, "Create"
    )

    assert built.plugins_ == ["a"]
    assert built.self_ == "me"
    # Members of nested structures are not parameters, so they keep their names.
    assert registry.build("Connector")(plugins=["a"], self="me").plugins == ["a"]


def test_escaped_input_member_does_not_collide_with_an_existing_name() -> None:
    schema = _input("CreateInput", ("plugins", STRING), ("plugins_", STRING))
    registry = _registry(CREATE_INPUT=schema)

    built = registry.build_input(
        hydrate(schema), {"plugins__": "escaped", "plugins_": "modeled"}, "Create"
    )

    assert (built.plugins__, built.plugins_) == ("escaped", "modeled")


def test_dict_names_resolve_to_dict_at_runtime() -> None:
    registry = _nested_registry()

    assert registry.build("PolicyDict") is dict
    assert registry.build("NestedInputDict") is dict
    assert registry.build("BlockDict") is dict
    assert registry.build("BlockTextDict") is dict
    with pytest.raises(AttributeError):
        registry.build("MissingDict")
    with pytest.raises(AttributeError):
        registry.build("Dict")
    # The former Params suffix is not kept as an alias.
    with pytest.raises(AttributeError):
        registry.build("PolicyParams")


def test_dict_name_never_shadows_a_modeled_shape() -> None:
    thing = _struct("Thing", ("Name", STRING))
    thing_dict = _struct("ThingDict", ("Name", STRING))
    registry = _registry(THING=thing, THING_DICT=thing_dict)

    assert registry.build("ThingDict").__name__ == "ThingDict"
    # The generator disambiguates the dictionary form of Thing with an underscore.
    assert registry.build("Thing_Dict") is dict
    assert registry.build("ThingDictDict") is dict


def test_modeled_shape_named_like_old_params_form_stays_a_model() -> None:
    thing_params = _struct("ThingParams", ("Name", STRING))
    registry = _registry(THING_PARAMS=thing_params)

    assert registry.build("ThingParams").__name__ == "ThingParams"
    assert registry.build("ThingParamsDict") is dict


def test_dict_name_keeps_the_underscores_of_its_shape() -> None:
    bar = _struct("Bar_", ("Name", STRING))
    registry = _registry(BAR_=bar)

    assert registry.build("Bar_").__name__ == "Bar_"
    assert registry.build("Bar_Dict") is dict
    # Disambiguated from a modeled Bar_Dict shape by one more underscore.
    assert registry.build("Bar__Dict") is dict
    with pytest.raises(AttributeError):
        registry.build("BarDict")


def test_dict_name_of_the_prelude_unit_shape_resolves() -> None:
    registry = _nested_registry()

    assert registry.build("UnitDict") is dict
    assert registry.build("Unit").__name__ == "Unit"


def test_async_dict_name_resolves_for_an_input_with_a_streaming_body() -> None:
    stream = (ShapeType.BLOB.value, NS, "Stream", {"smithy.api#streaming": None})
    upload = _input("UploadInput", ("Name", STRING), ("Body", stream))
    registry = _registry(UPLOAD_INPUT=upload, POLICY=POLICY)

    assert registry.build("UploadInputDict") is dict
    assert registry.build("AsyncUploadInputDict") is dict
    # Only an input with a streaming body has a form for each client.
    with pytest.raises(AttributeError):
        registry.build("AsyncPolicyDict")


def test_member_of_a_renamed_shape_takes_the_renamed_model() -> None:
    # Two shapes share an ID name across namespaces; the service renames one.
    greeting = _struct("Greeting", ("Hi", STRING))
    other: StaticSchema = (
        ShapeType.STRUCTURE.value,
        "ns.other",
        "Greeting",
        0,
        ("Salutation",),
        ((STRING, 0),),
    )
    schema = _input("GreetInput", ("Plain", greeting), ("Renamed", other))
    module = ModuleType(f"{NS}._private.schemas")
    module.GREETING = greeting  # type: ignore[attr-defined]
    module.RENAMED_GREETING = other  # type: ignore[attr-defined]
    module.GREET_INPUT = schema  # type: ignore[attr-defined]
    registry = ModelRegistry(
        module,
        renames={"RenamedGreeting": "RENAMED_GREETING"},
        index={"Greeting": "GREETING", "GreetInput": "GREET_INPUT"},
    )
    renamed = registry.build("RenamedGreeting")(salutation="hello")

    built = registry.build_input(
        hydrate(schema),
        {"plain": {"hi": "a"}, "renamed": {"salutation": "b"}},
        "Greet",
    )
    passed = registry.build_input(hydrate(schema), {"renamed": renamed}, "Greet")

    assert built.plain == registry.build("Greeting")(hi="a")
    assert built.renamed == registry.build("RenamedGreeting")(salutation="b")
    assert passed.renamed is renamed
