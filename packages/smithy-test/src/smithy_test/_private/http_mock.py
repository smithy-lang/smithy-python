#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
import inspect
import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from copy import deepcopy
from typing import Any, Protocol, cast
from urllib.parse import parse_qsl

from smithy_core._client import ClientBase
from smithy_core.exceptions import SmithyError
from smithy_http.interfaces import HTTPRequest

MOCK_CREDENTIAL = "HTTP_MOCK"


class MockTransport(Protocol):
    """A mock transport, holding the config transports it replaced."""

    displaced: list[Any]


class NoResponse(SmithyError):
    """Ends a call whose matching expectation has no response."""


def take_over(
    client: ClientBase[Any],
    transport: MockTransport,
    wrap_invoke: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> None:
    """Route the client's calls to the transport and replace its credentials.

    :raises TypeError: If the client's internals aren't the ones this relies on.
    """
    _check_client(client)
    # Typed as Any so instance attributes can shadow the client's methods.
    target: Any = client
    if target._setup_done:
        _scrub(target._config, transport)
        target._transport = transport
    elif target._config is not None:
        # Copied so the caller's config, possibly shared, keeps its own values.
        target._config = deepcopy(target._config)
        _scrub(target._config, transport)

    post_setup = target._post_setup
    build_call = target._build_call

    # Client and operation plugins may set credentials or a transport after this.
    def _post_setup(config: Any) -> Any:
        _scrub(config, transport)
        return post_setup(config)

    def _build_call(
        input: Any, operation: Any, *, config: Any, retry_strategy: Any
    ) -> Any:
        _scrub(config, transport)
        return build_call(
            input, operation, config=config, retry_strategy=retry_strategy
        )

    target._post_setup = _post_setup
    target._build_call = _build_call
    target._invoke = wrap_invoke(target._invoke)


def mismatches(
    matchers: dict[str, Any], request: HTTPRequest, body: bytes
) -> tuple[list[str], Exception | None]:
    """Describe each matcher the request fails, with the first error one raised."""
    failures: list[str] = []
    cause: Exception | None = None
    for label, matcher, subject in _subjects(matchers, request, body):
        if subject is _MISSING:
            failures.append(f"{label}: missing")
            continue
        try:
            if _matches(matcher, subject):
                continue
            failures.append(f"{label}: expected {matcher!r}, got {subject!r}")
        except Exception as e:
            failures.append(f"{label}: matcher raised {e!r}")
            cause = cause or e
    return failures, cause


_MISSING = object()

_CLIENT_ATTRIBUTES = ("_setup_done", "_config", "_transport")
_CLIENT_HOOKS = {
    "_post_setup": ("config",),
    "_build_call": ("input", "operation", "config", "retry_strategy"),
    "_invoke": ("input", "operation", "default_plugins", "plugins"),
}
_CREDENTIAL_FIELDS = ("aws_access_key_id", "aws_secret_access_key", "aws_session_token")


def _check_client(client: ClientBase[Any]) -> None:
    name = type(client).__name__
    missing = [a for a in _CLIENT_ATTRIBUTES if not hasattr(client, a)]
    if missing:
        raise TypeError(f"{name} has no {', '.join(missing)}; it can't be mocked.")
    for hook, parameters in _CLIENT_HOOKS.items():
        found = tuple(inspect.signature(getattr(client, hook)).parameters)
        if found != parameters:
            raise TypeError(
                f"{name}.{hook} takes {found}, but the mock expects {parameters}."
            )


def _check_config(config: Any) -> None:
    name = type(config).__name__
    if not hasattr(config, "transport"):
        raise TypeError(f"{name} has no transport; it can't be mocked.")
    aws = ("aws_credentials_identity_resolver", *_CREDENTIAL_FIELDS)
    present = [f for f in aws if hasattr(config, f)]
    if not present:
        return
    if len(present) < len(aws) or not callable(
        getattr(config, "_static_credentials_resolver", None)
    ):
        raise TypeError(
            f"{name} has the AWS credential fields {present}, but the mock needs all "
            f"of {list(aws)} and _static_credentials_resolver to replace them."
        )


def _scrub(config: Any, transport: MockTransport) -> None:
    _check_config(config)
    source_of = getattr(config, "source_of", None)
    # A default transport belongs to the config, so the mock closes it in its place.
    if (
        config.transport is not transport
        and source_of is not None
        and source_of("transport") == "default"
    ):
        transport.displaced.append(config.transport)
    config.transport = transport
    if hasattr(config, "aws_credentials_identity_resolver"):
        # Imported here so clients without AWS auth don't need smithy-aws-core.
        from smithy_aws_core.identity.components import AWSCredentialsIdentity

        # CAUTION: bypasses AwsConfig.__setattr__, which locks resolved credentials.
        for name in _CREDENTIAL_FIELDS:
            object.__setattr__(config, name, MOCK_CREDENTIAL)
        config.aws_credentials_identity_resolver = config._static_credentials_resolver(
            AWSCredentialsIdentity(
                access_key_id=MOCK_CREDENTIAL,
                secret_access_key=MOCK_CREDENTIAL,
                session_token=MOCK_CREDENTIAL,
            )
        )


def _subjects(
    matchers: dict[str, Any], request: HTTPRequest, body: bytes
) -> Iterator[tuple[str, Any, Any]]:
    uri = request.destination
    scalars: dict[str, Any] = {
        "method": request.method,
        "scheme": uri.scheme,
        "hostname": uri.host,
        "port": uri.port,
        "path": uri.path or "",
        "body": body,
    }
    entries = {
        "query": _join(parse_qsl(uri.query or "", keep_blank_values=True)),
        "headers": _join((f.name.lower(), v) for f in request.fields for v in f.values),
    }
    for name, matcher in matchers.items():
        if name in scalars:
            yield name, matcher, scalars[name]
        elif not isinstance(matcher, Mapping):
            yield name, matcher, entries[name]
        else:
            for key, entry_matcher in cast(Mapping[str, Any], matcher).items():
                # Header names are case-insensitive; query keys aren't.
                lookup = key.lower() if name == "headers" else key
                yield (
                    f"{name}[{key!r}]",
                    entry_matcher,
                    entries[name].get(lookup, _MISSING),
                )


def _matches(matcher: Any, subject: Any) -> bool:
    if isinstance(matcher, str):
        text = _text(subject)
        if len(matcher) >= 2 and matcher.startswith("/") and matcher.endswith("/"):
            return re.search(matcher[1:-1], text) is not None
        return text == matcher
    result = matcher(subject)
    return result is True or result is None


def _join(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    joined: dict[str, list[str]] = {}
    for key, value in pairs:
        joined.setdefault(key, []).append(value)
    return {key: ",".join(values) for key, values in joined.items()}


def _text(subject: Any) -> str:
    if subject is None:
        return ""
    if isinstance(subject, bytes):
        return subject.decode("utf-8", errors="replace")
    return str(subject)
