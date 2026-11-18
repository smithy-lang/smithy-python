# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import base64
import struct
from collections.abc import Mapping
from typing import Any

import pytest
from smithy_core.endpoints import BddEndpointResolver, EndpointBdd
from smithy_python._endpoints import (
    MANUAL_ENDPOINT_BDD,
    EndpointPlan,
    client_context_fields,
    literal,
    lower,
    plan_endpoints,
    write_endpoints,
)
from smithy_python.exceptions import CodegenError
from smithy_python.model import Node, ServiceShape, load_model
from smithy_python.writer import PythonWriter

_PARAMETERS = {
    "Region": {
        "type": "String",
        "builtIn": "AWS::Region",
        "documentation": "The region.",
    },
    "UseFIPS": {
        "type": "Boolean",
        "required": True,
        "default": False,
        "builtIn": "AWS::UseFIPS",
        "deprecated": {"message": "old"},
    },
    "Endpoint": {"type": "string", "builtIn": "SDK::Endpoint"},
    "Key": {"type": "string"},
    "Bucket": {"type": "String", "required": True},
    "ForcePathStyle": {"type": "boolean", "builtIn": "AWS::S3::ForcePathStyle"},
    "Tables": {"type": "stringArray", "required": True, "default": ["a", "b"]},
    "Unused": {"type": "boolean", "default": True, "required": True},
}

_CONDITIONS: list[Any] = [
    {"fn": "isSet", "argv": [{"ref": "Endpoint"}]},
    {"fn": "parseURL", "argv": ["{Endpoint}"], "assign": "url"},
    {"fn": "booleanEquals", "argv": [{"ref": "UseFIPS"}, True]},
    {
        "fn": "stringEquals",
        "argv": [{"fn": "getAttr", "argv": [{"ref": "url"}, "scheme"]}, "http"],
    },
    {"fn": "isSet", "argv": [{"ref": "Region"}]},
    {"fn": "isValidHostLabel", "argv": [{"ref": "Region"}, False]},
    {
        "fn": "stringEquals",
        "argv": [
            {
                "fn": "coalesce",
                "argv": [
                    {"fn": "substring", "argv": [{"ref": "Bucket"}, 0, 4, False]},
                    "",
                ],
            },
            "ab{{c}}",
        ],
    },
    {"fn": "split", "argv": [{"ref": "Bucket"}, "--", 0], "assign": "parts"},
    {"fn": "isSet", "argv": [{"fn": "getAttr", "argv": [{"ref": "parts"}, "[-1]"]}]},
    {
        "fn": "ite",
        "argv": [
            {"fn": "coalesce", "argv": [{"ref": "ForcePathStyle"}, False]},
            "path",
            "vhost",
        ],
        "assign": "style",
    },
]

_RESULTS: list[Any] = [
    {
        "conditions": [],
        "type": "error",
        "error": "Invalid {Region}: {{escaped}} {Bucket}{Bucket}",
    },
    {
        "conditions": [],
        "type": "endpoint",
        "endpoint": {
            "url": "{url#scheme}://{url#authority}{url#path}",
            "properties": {
                "authSchemes": [
                    {
                        "name": "sigv4",
                        "signingRegion": "{Region}",
                        "disableDoubleEncoding": True,
                    }
                ],
                "literal": {
                    "ref": "Region",
                    "fn": "isSet",
                    "n": 2,
                    "list": ["{style}", ["x"]],
                },
            },
            "headers": {"x-b": ["{Region}", "b"], "x-a": []},
        },
    },
    {
        "conditions": [],
        "type": "endpoint",
        "endpoint": {"url": {"ref": "Endpoint"}, "properties": {}, "headers": {}},
    },
    {
        "conditions": [],
        "type": "endpoint",
        "endpoint": {"url": "https://{Bucket}.example.com"},
    },
]

_NODES = (-1, 1, -1, 0, 3, 100_000_003, 1, 100_000_002, 100_000_001)


def _raw_trait(
    parameters: Mapping[str, Any] = _PARAMETERS,
    conditions: list[Any] = _CONDITIONS,
    results: list[Any] = _RESULTS,
    root: int = 2,
    nodes: tuple[int, ...] = _NODES,
    version: str = "1.1",
) -> dict[str, Any]:
    return {
        "version": version,
        "parameters": parameters,
        "conditions": conditions,
        "results": results,
        "root": root,
        "nodeCount": len(nodes) // 3,
        "nodes": base64.b64encode(struct.pack(f">{len(nodes)}i", *nodes)).decode(),
    }


def _trait(**changes: Any) -> Mapping[str, Node]:
    service = _service({"smithy.rules#endpointBdd": _raw_trait(**changes)})
    value = service.get_trait("smithy.rules#endpointBdd")
    assert isinstance(value, Mapping)
    return value


def _service(traits: Mapping[str, Any]) -> ServiceShape:
    model = load_model(
        {
            "smithy": "2.0",
            "shapes": {"example#Service": {"type": "service", "traits": traits}},
        }
    )
    return model.expect_shape("example#Service", ServiceShape)


def _lines(items: tuple[Any, ...]) -> list[str]:
    return [literal(item) for item in items]


def test_rejects_other_trait_versions() -> None:
    with pytest.raises(CodegenError, match=r"version 1\.2"):
        lower(_trait(version="1.2"), {})


def test_normalizes_and_drops_parameters() -> None:
    bdd = lower(_trait(), {"ForcePathStyle": "path_style"})
    # Key is optional and unread, so it is dropped. Unused and Tables are required.
    assert literal(bdd.parameters) == (
        '(("Region", "string", False, None, "AWS::Region", None), '
        '("UseFIPS", "boolean", True, False, "AWS::UseFIPS", None), '
        '("Endpoint", "string", False, None, "SDK::Endpoint", None), '
        '("Bucket", "string", True, None, None, None), '
        '("ForcePathStyle", "boolean", False, None, "AWS::S3::ForcePathStyle", '
        '"path_style"), '
        '("Tables", "stringArray", True, ("a", "b"), None, None), '
        '("Unused", "boolean", True, True, None, None))'
    )


def test_keeps_parameters_read_as_get_attr_bases() -> None:
    bdd = lower(
        _trait(
            parameters={
                "A": {"type": "string"},
                "T": {"type": "stringArray"},
                "C": {"type": "string"},
            },
            conditions=[
                {"fn": "isSet", "argv": [{"ref": "A"}]},
                {"fn": "isSet", "argv": [{"ref": "T"}]},
                {
                    "fn": "isSet",
                    "argv": [{"fn": "getAttr", "argv": [{"ref": "T"}, "[0]"]}],
                },
            ],
            results=[{"conditions": [], "type": "error", "error": "{A}"}],
            root=100_000_001,
            nodes=(-1, 1, -1),
        ),
        {},
    )
    # C is optional and unread, so it is dropped.
    assert literal(bdd.parameters) == (
        '(("A", "string", False, None, None, None), '
        '("T", "stringArray", False, None, None, None))'
    )


def test_sorts_functions_by_code_point() -> None:
    assert lower(_trait(), {}).functions == (
        "booleanEquals",
        "coalesce",
        "isSet",
        "isValidHostLabel",
        "ite",
        "parseURL",
        "split",
        "stringEquals",
        "substring",
    )


def test_lowers_conditions() -> None:
    conditions = _lines(lower(_trait(), {}).conditions)
    assert conditions[0] == '((2, "isSet", (0, "Endpoint")), None)'
    # A string argument that is a single placeholder is still a template.
    assert conditions[1] == '((2, "parseURL", "{Endpoint}"), "url")'
    assert conditions[2] == '((2, "booleanEquals", (0, "UseFIPS"), True), None)'
    assert conditions[3] == (
        '((2, "stringEquals", (1, (0, "url"), "scheme"), "http"), None)'
    )
    assert conditions[5] == '((2, "isValidHostLabel", (0, "Region"), False), None)'
    # Literal strings keep their escaped braces, and integers stay integers.
    assert conditions[6] == (
        '((2, "stringEquals", (2, "coalesce", '
        '(2, "substring", (0, "Bucket"), 0, 4, False), ""), "ab{{c}}"), None)'
    )
    assert conditions[7] == '((2, "split", (0, "Bucket"), "--", 0), "parts")'
    # A negative index counts from the end.
    assert conditions[8] == '((2, "isSet", (1, (0, "parts"), "[-1]")), None)'
    assert conditions[9] == (
        '((2, "ite", (2, "coalesce", (0, "ForcePathStyle"), False), '
        '"path", "vhost"), "style")'
    )


def test_lowers_results() -> None:
    results = _lines(lower(_trait(), {}).results)
    assert results[0] == "None"
    assert results[1] == '(5, "Invalid {Region}: {{escaped}} {Bucket}{Bucket}")'
    # Objects in properties are maps even with ref or fn keys. Header order is kept.
    assert results[2] == (
        '(6, "{url#scheme}://{url#authority}{url#path}", '
        '(4, ("authSchemes", "literal"), '
        '(3, (4, ("name", "signingRegion", "disableDoubleEncoding"), "sigv4", '
        '"{Region}", True)), '
        '(4, ("ref", "fn", "n", "list"), "Region", "isSet", 2, '
        '(3, "{style}", (3, "x")))), '
        '(("x-b", ("{Region}", "b")), ("x-a", ())))'
    )
    # Empty properties become None and empty headers ().
    assert results[3] == '(6, (0, "Endpoint"), None, ())'
    assert results[4] == '(6, "https://{Bucket}.example.com", None, ())'
    assert len(results) == 5


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{{{url#authority} }} {Endpoint}{{}}", "{{{url#authority} }} {Endpoint}{{}}"),
        ("{url#a.b[1]}", "{url#a.b[1]}"),
        ("{url#[+1]}", "{url#[1]}"),
        ("{url#.a}", "{url#a}"),
    ],
)
def test_renders_templates_from_their_parsed_parts(
    template: str, expected: str
) -> None:
    bdd = lower(
        _trait(
            parameters={"Endpoint": {"type": "string", "required": True}},
            conditions=[
                {"fn": "parseURL", "argv": [{"ref": "Endpoint"}], "assign": "url"}
            ],
            results=[{"conditions": [], "type": "error", "error": template}],
            nodes=(-1, 1, -1, 0, 100_000_001, 1),
        ),
        {},
    )
    assert bdd.results[1] == (5, expected)


@pytest.mark.parametrize(
    ("template", "message"),
    [
        ("{a", "unmatched {"),
        ("a}", "unmatched }"),
        ("{url#a[x]}", "invalid getAttr path"),
        ("{url#.}", "empty getAttr path"),
    ],
)
def test_rejects_malformed_templates(template: str, message: str) -> None:
    with pytest.raises(CodegenError, match=message):
        lower(
            _trait(
                results=[{"conditions": [], "type": "error", "error": template}],
                nodes=(-1, 1, -1),
                root=-1,
            ),
            {},
        )


def test_copies_nodes_verbatim() -> None:
    nodes = (-1, 1, -1, 0, -3, 1, 1, 100_000_001, -1)
    assert lower(_trait(nodes=nodes), {}).nodes == nodes


def test_accepts_terminal_root() -> None:
    bdd = lower(_trait(root=-1, nodes=(-1, 1, -1)), {})
    assert bdd.root == -1
    assert bdd.nodes == (-1, 1, -1)


@pytest.mark.parametrize(
    ("nodes", "message"),
    [
        ((-1, 1, -1, 0, -100_000_001, 1), "node 1 complements a result reference"),
        ((0, 1, -1, 0, 1, -1), "node 0"),
    ],
)
def test_rejects_invalid_nodes(nodes: tuple[int, ...], message: str) -> None:
    with pytest.raises(CodegenError, match=message):
        lower(_trait(nodes=nodes), {})


def test_rejects_results_with_conditions() -> None:
    results = [{**_RESULTS[0], "conditions": [_CONDITIONS[0]]}]
    with pytest.raises(CodegenError, match="result 1 has conditions"):
        lower(_trait(results=results), {})


def test_renders_literals() -> None:
    assert literal(()) == "()"
    assert literal(("a",)) == '("a",)'
    assert literal((None, True, False, -5)) == "(None, True, False, -5)"
    assert literal('q"b\\n\n\t\x01é😀') == '"q\\"b\\\\n\\n\\t\\x01\\u00e9\\U0001f600"'


def test_writes_the_endpoints_module() -> None:
    trait = _trait(
        parameters={"Endpoint": {"type": "string", "builtIn": "SDK::Endpoint"}},
        conditions=[{"fn": "isSet", "argv": [{"ref": "Endpoint"}]}],
        results=[
            {
                "conditions": [],
                "type": "endpoint",
                "endpoint": {"url": {"ref": "Endpoint"}},
            },
            {"conditions": [], "type": "error", "error": "no endpoint"},
        ],
        nodes=(-1, 1, -1, 0, 100_000_001, 100_000_002),
    )
    writer = PythonWriter("example._private.endpoints")
    write_endpoints(writer, EndpointPlan(trait, lower(trait, {}), ()))
    assert writer.render() == (
        "from smithy_core.endpoints import EndpointBdd\n"
        "\n"
        "\n"
        "# fmt: off\n"
        "# Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.\n"
        "BDD = EndpointBdd(\n"
        "    # (name, type, required, default, builtin, client_context_attribute)\n"
        "    parameters=(\n"
        '        ("Endpoint", "string", False, None, "SDK::Endpoint", None),\n'
        "    ),\n"
        '    functions=("isSet",),\n'
        "    conditions=(\n"
        '        ((2, "isSet", (0, "Endpoint")), None),  # 0: isSet(Endpoint)\n'
        "    ),\n"
        "    results=(\n"
        "        None,  # 0: no match\n"
        '        (6, (0, "Endpoint"), None, ()),  # 1\n'
        '        (5, "no endpoint"),  # 2\n'
        "    ),\n"
        "    root=2,\n"
        "    # (condition, high, low); 1 and -1 are terminals, a negative reference"
        " is a\n"
        "    # complement edge, and 100_000_000 + k is result k.\n"
        "    nodes=(\n"
        "        -1, 1, -1,\n"
        "        0, 100_000_001, 100_000_002,\n"
        "    ),\n"
        ")\n"
        "# fmt: on\n"
    )


def test_written_bdd_evaluates_with_smithy_core() -> None:
    trait = _trait()
    writer = PythonWriter("example._private.endpoints")
    write_endpoints(writer, EndpointPlan(trait, lower(trait, {}), ()))
    namespace: dict[str, Any] = {}
    exec(writer.render(), namespace)
    assert isinstance(namespace["BDD"], EndpointBdd)
    BddEndpointResolver(namespace["BDD"])


def test_a_service_without_rules_requires_an_endpoint() -> None:
    plan = plan_endpoints(_service({}))
    assert plan.trait is MANUAL_ENDPOINT_BDD
    assert plan.bdd.parameters == (
        ("endpoint", "string", False, None, "SDK::Endpoint", None),
    )
    assert plan.bdd.results[2] == (
        5,
        "(default endpointRuleSet) endpoint is not set - you must configure an "
        "endpoint.",
    )


def test_a_ruleset_without_a_bdd_is_rejected() -> None:
    with pytest.raises(CodegenError, match=r"smithy\.rules#endpointRuleSet without"):
        plan_endpoints(_service({"smithy.rules#endpointRuleSet": {}}))


def test_functions_outside_the_standard_library_are_rejected() -> None:
    conditions = [{"fn": "aws.partition", "argv": ["us-east-1"], "assign": "p"}]
    trait = _raw_trait(conditions=conditions, root=-1, nodes=(-1, 1, -1))
    with pytest.raises(CodegenError, match=r"call aws\.partition"):
        plan_endpoints(_service({"smithy.rules#endpointBdd": trait}))


def test_client_context_fields_are_snake_case_config_fields() -> None:
    service = _service(
        {
            "smithy.rules#clientContextParams": {
                "ForcePathStyle": {"type": "boolean", "documentation": "Path style."},
                "UseFIPS": {"type": "boolean"},
                "Stage": {"type": "string"},
            }
        }
    )
    fields = client_context_fields(service)
    assert [(f.parameter, f.attribute, f.type) for f in fields] == [
        ("ForcePathStyle", "force_path_style", "bool"),
        ("UseFIPS", "use_fips", "bool"),
        ("Stage", "stage", "str"),
    ]
    assert fields[0].documentation == "Path style."
    assert fields[1].documentation == "The UseFIPS endpoint parameter."


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"Tables": {"type": "stringArray"}}, "Unsupported type stringArray"),
        ({"Protocol": {"type": "string"}}, "which the config already has"),
        (
            {"UseFips": {"type": "boolean"}, "UseFIPS": {"type": "boolean"}},
            "which UseFips also maps to",
        ),
    ],
)
def test_client_context_fields_must_be_supported_and_distinct(
    parameters: Mapping[str, Any], message: str
) -> None:
    service = _service({"smithy.rules#clientContextParams": parameters})
    with pytest.raises(CodegenError, match=message):
        client_context_fields(service, reserved={"protocol"})
