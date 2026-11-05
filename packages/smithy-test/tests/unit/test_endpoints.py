#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any

import pytest
from smithy_core import URI
from smithy_core.aio.endpoints import AsyncBddEndpointResolver
from smithy_core.documents import Document
from smithy_core.endpoints import (
    RESOLVED_ENDPOINT,
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
from smithy_test.aio import check_client_case_async, check_rules_case_async

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


def _resolver() -> AsyncBddEndpointResolver:
    return AsyncBddEndpointResolver(BDD, extensions=[EXTENSION])


async def test_rules_cases_resolve_only_the_given_values() -> None:
    await check_rules_case_async(
        _resolver(),
        {"Region": "us-west-2", "Bucket": "b"},
        ENDPOINT,
        extensions=[EXTENSION],
    )
    await check_rules_case_async(_resolver(), {}, {"error": "Missing Region"})


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
async def test_rules_cases_fail_on_mismatches(
    params: dict[str, Any], expect: dict[str, Any], message: str
) -> None:
    with pytest.raises(AssertionError, match=message):
        await check_rules_case_async(
            _resolver(), params, expect, extensions=[EXTENSION]
        )


class _Request:
    def __init__(self, destination: URI) -> None:
        self.destination = destination


class _Client:
    """Runs the hook the capture interceptor uses, as the request pipeline does."""

    ENDPOINT = Endpoint(uri=URI(host="h.example.com", path="/p", query="a=b"))

    def __init__(self, interceptor: Interceptor[Any, Any, Any, Any]) -> None:
        self.interceptor = interceptor

    async def send(self, destination: URI) -> None:
        properties = TypedProperties()
        properties[RESOLVED_ENDPOINT] = self.ENDPOINT
        context: RequestContext[Any, Any] = RequestContext(
            request=Document(),
            transport_request=_Request(destination),
            properties=properties,
        )
        self.interceptor.read_before_signing(context)

    async def fail(self, input: None) -> None:
        raise EndpointResolutionError("Missing Region")

    async def complete(self, input: None) -> None:
        pass


async def _client(interceptor: Interceptor[Any, Any, Any, Any]) -> _Client:
    return _Client(interceptor)


CLIENT_ENDPOINT = {"endpoint": {"url": "https://h.example.com/p?a=b"}}


async def test_client_cases_check_the_captured_endpoint_and_request() -> None:
    destination = URI(host="h.example.com", path="/p/op", query="a=b&x=y")
    await check_client_case_async(_client, _Client.send, destination, CLIENT_ENDPOINT)


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
            _client, _Client.send, destination, CLIENT_ENDPOINT
        )


async def test_client_cases_check_resolution_errors() -> None:
    await check_client_case_async(
        _client, _Client.fail, None, {"error": "Missing Region"}
    )
    with pytest.raises(AssertionError, match="got the error Missing Region"):
        await check_client_case_async(
            _client, _Client.fail, None, {"endpoint": {"url": "https://h.example.com"}}
        )


async def test_client_cases_fail_when_no_endpoint_is_resolved() -> None:
    with pytest.raises(AssertionError, match="without resolving an endpoint"):
        await check_client_case_async(
            _client, _Client.complete, None, {"error": "Missing Region"}
        )
