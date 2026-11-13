#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

import pytest
from smithy_core import URI
from smithy_core.documents import Document
from smithy_core.endpoints import (
    HOST_PREFIX,
    RESOLVED_ENDPOINT,
    BddEndpointResolver,
    Endpoint,
    EndpointAuthScheme,
    EndpointBdd,
    RulesExtension,
)
from smithy_core.endpoints._types import Tag
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.interceptors import Interceptor, RequestContext
from smithy_core.shapes import ShapeID
from smithy_core.types import TypedProperties
from smithy_test import check_rules_case
from smithy_test.aio import check_client_case_async

# isSet(Region) gives a regional endpoint with properties and headers, else an error.
BDD = EndpointBdd(
    parameters=(
        ("Region", "string", False, None, "X::Region", None),
        ("Bucket", "string", False, None, None, None),
    ),
    functions=("isSet",),
    conditions=(((Tag.CALL, "isSet", (Tag.REF, "Region")), None),),
    results=(
        None,
        (
            Tag.ENDPOINT,
            "https://{Region}.example.com",
            (
                Tag.MAP,
                ("authSchemes", "backend"),
                (Tag.LIST, (Tag.MAP, ("name", "signingRegion"), "sigv4", "{Region}")),
                (Tag.LIST, "a", "{Bucket}"),
            ),
            (("x-region", ("{Region}",)),),
        ),
        (Tag.ERROR, "Missing Region"),
    ),
    root=2,
    nodes=(-1, 1, -1, 0, 100_000_001, 100_000_002),
)

ENDPOINT = {
    "endpoint": {
        "url": "https://us-west-2.example.com",
        "headers": {"x-region": ["us-west-2"]},
        "properties": {
            "authSchemes": [{"name": "sigv4", "signingRegion": "us-west-2"}],
            "backend": ["a", "b"],
        },
    }
}


def _sigv4(entry: Mapping[str, Any]) -> EndpointAuthScheme:
    return EndpointAuthScheme(
        scheme_id=ShapeID("x.auth#sigv4"),
        properties=TypedProperties({"region": entry["signingRegion"]}),
    )


# The built-in binding is set so the check shows it binds nothing from config.
EXTENSION = RulesExtension(
    builtins={"X::Region": "region"}, auth_schemes={"sigv4": _sigv4}
)


def _resolver() -> BddEndpointResolver:
    return BddEndpointResolver(BDD, extensions=[EXTENSION])


def test_rules_cases_resolve_only_the_given_values() -> None:
    check_rules_case(
        _resolver(),
        {"Region": "us-west-2", "Bucket": "b"},
        ENDPOINT,
        extensions=[EXTENSION],
    )
    check_rules_case(_resolver(), {}, {"error": "Missing Region"})


@pytest.mark.parametrize(
    "params, expect, message",
    [
        (
            {"Region": "us-east-1", "Bucket": "b"},
            ENDPOINT,
            "Expected url 'https://us-west-2.example.com'",
        ),
        ({"Region": "us-west-2", "Bucket": "c"}, ENDPOINT, "Expected properties"),
        (
            {"Region": "us-west-2", "Bucket": "b"},
            {"endpoint": {"url": "https://us-west-2.example.com"}},
            "Expected authSchemes \\[\\]",
        ),
        (
            {"Region": "us-west-2", "Bucket": "b"},
            {"error": "Missing Region"},
            "Expected the error 'Missing Region'",
        ),
        ({}, ENDPOINT, "got the error Missing Region"),
        ({}, {"error": "Other"}, "Expected error 'Other'"),
    ],
)
def test_rules_cases_fail_on_mismatches(
    params: dict[str, Any], expect: dict[str, Any], message: str
) -> None:
    with pytest.raises(AssertionError, match=message):
        check_rules_case(_resolver(), params, expect, extensions=[EXTENSION])


class _Request:
    def __init__(self, destination: URI) -> None:
        self.destination = destination


class _Client:
    """Runs the hook the capture interceptor uses, as the request pipeline does.

    Its operations take keyword arguments only, as a generated client's do.
    """

    ENDPOINT = Endpoint(uri=URI(host="h.example.com", path="/p", query="a=b"))

    def __init__(self, interceptor: Interceptor[Any, Any, Any, Any]) -> None:
        self.interceptor = interceptor

    async def send(
        self, *, destination: URI, properties: TypedProperties | None = None
    ) -> None:
        properties = properties or TypedProperties()
        properties[RESOLVED_ENDPOINT] = self.ENDPOINT
        context: RequestContext[Any, Any] = RequestContext(
            request=Document(),
            transport_request=_Request(destination),
            properties=properties,
        )
        self.interceptor.read_before_signing(context)

    async def send_with_host_prefix(self, *, destination: URI) -> None:
        await self.send(
            destination=destination,
            properties=TypedProperties({HOST_PREFIX.key: "data."}),
        )

    async def fail(self) -> None:
        raise EndpointResolutionError("Missing Region")

    async def complete(self) -> None:
        pass


async def _client(interceptor: Interceptor[Any, Any, Any, Any]) -> _Client:
    return _Client(interceptor)


CLIENT_ENDPOINT = {"endpoint": {"url": "https://h.example.com/p?a=b"}}


async def test_client_cases_check_the_captured_endpoint_and_request() -> None:
    destination = URI(host="h.example.com", path="/p/op", query="a=b&x=y")
    await check_client_case_async(
        _client, _Client.send, {"destination": destination}, CLIENT_ENDPOINT
    )


async def test_client_cases_pass_the_input_as_keyword_arguments() -> None:
    calls: list[dict[str, Any]] = []

    async def operation(
        client: _Client, *, name: str, tag: object, plugins: None = None
    ) -> None:
        calls.append({"name": name, "tag": tag, "plugins": plugins})
        raise EndpointResolutionError("Missing Region")

    # A read-only mapping shows the input is unpacked, not changed, and a value
    # that is a model is handed to the operation as the same object.
    tag = object()
    input = MappingProxyType({"name": "n", "tag": tag})
    await check_client_case_async(
        _client, operation, input, {"error": "Missing Region"}
    )

    assert calls == [{"name": "n", "tag": tag, "plugins": None}]
    assert calls[0]["tag"] is tag


async def test_client_cases_reject_input_the_operation_does_not_take() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument 'unknown'"):
        await check_client_case_async(
            _client, _Client.fail, {"unknown": 1}, {"error": "Missing Region"}
        )


@pytest.mark.parametrize(
    "destination",
    [
        URI(host="prefix.h.example.com", path="/p", query="a=b"),
        URI(host="h.example.com", path="/op", query="a=b"),
        URI(host="h.example.com", path="/pop", query="a=b"),
        URI(host="h.example.com", path="/p/op", query="x=y"),
    ],
)
async def test_client_cases_fail_on_requests_outside_the_endpoint(
    destination: URI,
) -> None:
    with pytest.raises(AssertionError, match="Expected request destination"):
        await check_client_case_async(
            _client, _Client.send, {"destination": destination}, CLIENT_ENDPOINT
        )


async def test_client_cases_expect_the_host_prefix_on_the_destination() -> None:
    destination = URI(host="data.h.example.com", path="/p", query="a=b")
    await check_client_case_async(
        _client,
        _Client.send_with_host_prefix,
        {"destination": destination},
        CLIENT_ENDPOINT,
    )

    with pytest.raises(AssertionError, match=r"with host prefix 'data\.'"):
        await check_client_case_async(
            _client,
            _Client.send_with_host_prefix,
            {"destination": URI(host="h.example.com", path="/p", query="a=b")},
            CLIENT_ENDPOINT,
        )


async def test_client_cases_check_resolution_errors() -> None:
    await check_client_case_async(
        _client, _Client.fail, {}, {"error": "Missing Region"}
    )
    with pytest.raises(AssertionError, match="got the error Missing Region"):
        await check_client_case_async(
            _client, _Client.fail, {}, {"endpoint": {"url": "https://h.example.com"}}
        )


async def test_client_cases_fail_when_no_endpoint_is_resolved() -> None:
    with pytest.raises(AssertionError, match="without resolving an endpoint"):
        await check_client_case_async(
            _client, _Client.complete, {}, {"error": "Missing Region"}
        )
