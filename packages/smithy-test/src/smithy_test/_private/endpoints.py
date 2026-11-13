#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Helpers for the ``smithy.rules#endpointTests`` checks in :py:mod:`smithy_test`."""

from collections.abc import Mapping, Sequence
from typing import Any

from smithy_core import URI
from smithy_core.endpoints import (
    ENDPOINT_HEADERS,
    HOST_PREFIX,
    RESOLVED_ENDPOINT,
    RulesExtension,
)
from smithy_core.exceptions import SmithyError
from smithy_core.interceptors import Interceptor, RequestContext
from smithy_core.interfaces import Endpoint
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType


class UnboundConfig:
    """A config with no fields, so no built-in or client context parameter is bound."""

    endpoint_uri: str | URI | None = None


# An operation with no traits and no input members, so no parameter is bound.
UNBOUND_OPERATION: APIOperation[Any, Any] = APIOperation(
    static_schema=(
        ShapeType.OPERATION.value,
        "smithy.test",
        "EndpointRules",
        0,
        (ShapeType.STRUCTURE.value, "smithy.test", "EndpointRulesInput", 0, (), ()),
        -1,
        (),
    ),
)


class EndpointCaptured(SmithyError):
    """Stops a call once its endpoint is applied to the request."""

    def __init__(self, endpoint: Endpoint, request: Any, host_prefix: str) -> None:
        super().__init__("Endpoint captured")
        self.endpoint = endpoint
        self.request = request
        self.host_prefix = host_prefix


class CaptureEndpoint(Interceptor[Any, Any, Any, Any]):
    """Stops a call at the first hook after its endpoint is applied to the request."""

    def read_before_signing(self, context: RequestContext[Any, Any]) -> None:
        raise EndpointCaptured(
            context.properties[RESOLVED_ENDPOINT],
            context.transport_request,
            context.properties.get(HOST_PREFIX, ""),
        )


def check_endpoint(
    expect: Mapping[str, Any],
    endpoint: Endpoint,
    extensions: Sequence[RulesExtension],
) -> None:
    url = endpoint.uri.build()
    if "error" in expect:
        raise AssertionError(f"Expected the error {expect['error']!r}, got {url}")
    expected = expect["endpoint"]
    _check("url", url, expected["url"])
    expected_properties = dict(expected.get("properties", {}))
    _check(
        "authSchemes",
        [
            {"scheme_id": str(scheme.scheme_id), **scheme.properties}
            for scheme in endpoint.auth_schemes
        ],
        _expected_auth_schemes(expected_properties.pop("authSchemes", ()), extensions),
    )
    properties = dict(endpoint.properties.items())
    _check(
        "headers",
        properties.pop(ENDPOINT_HEADERS.key, {}),
        expected.get("headers", {}),
    )
    _check("properties", properties, expected_properties)


def check_error(expect: Mapping[str, Any], error: Exception) -> None:
    if "error" not in expect:
        raise AssertionError(
            f"Expected {expect['endpoint']['url']}, got the error {error}"
        ) from error
    _check("error", str(error), expect["error"])


def check_destination(endpoint: Endpoint, request: Any, host_prefix: str) -> None:
    destination = getattr(request, "destination", None)
    if destination is None:
        return
    uri = endpoint.uri
    if (
        (destination.scheme, destination.host, destination.port)
        != (uri.scheme, host_prefix + uri.host, uri.port)
        or not _extends(destination.path, (uri.path or "").rstrip("/"), "/")
        or not _extends(destination.query, uri.query, "&")
    ):
        prefixed = f" with host prefix {host_prefix!r}" if host_prefix else ""
        raise AssertionError(
            f"Expected request destination under {uri.build()}{prefixed},"
            f" got {destination.build()}"
        )


def _expected_auth_schemes(
    entries: Sequence[Mapping[str, Any]], extensions: Sequence[RulesExtension]
) -> list[dict[str, Any]]:
    """A case's expected ``authSchemes`` as resolution gives them: each entry built by
    its name's extension factory, and names no extension maps left out."""
    factories = {
        name: factory
        for extension in extensions
        for name, factory in extension.auth_schemes.items()
    }
    expected: list[dict[str, Any]] = []
    for entry in entries:
        factory = factories.get(entry["name"])
        if factory is not None:
            scheme = factory(entry)
            expected.append({"scheme_id": str(scheme.scheme_id), **scheme.properties})
    return expected


def _extends(value: str | None, base: str | None, separator: str) -> bool:
    """Whether a value is its base, or its base and separator followed by more."""
    if not base:
        return True
    return value == base or (value or "").startswith(base + separator)


def _check(name: str, actual: Any, expected: Any) -> None:
    # Rules values are tuples and read-only mappings; cases are lists and dicts.
    if _plain(actual) != _plain(expected):
        raise AssertionError(f"Expected {name} {expected!r}, got {actual!r}")


def _plain(value: Any) -> Any:
    if isinstance(value, tuple | list):
        return [_plain(v) for v in value]  # pyright: ignore[reportUnknownVariableType]
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType]
    return value
