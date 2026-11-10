#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The endpoint rules standard library functions the engine calls.

The engine compiles the other standard functions itself: ``isSet``, ``not``,
``booleanEquals``, ``stringEquals``, ``coalesce`` and ``ite``.
"""

from collections.abc import Callable, Mapping
from re import compile as _re
from types import MappingProxyType
from typing import Any
from urllib.parse import quote, urlsplit


def _substring(value: str | None, start: int, stop: int, reverse: bool) -> str | None:
    # A range that doesn't fit, including one with a negative start, gives None.
    if (
        value is None
        or start < 0
        or start >= stop
        or len(value) < stop
        or not value.isascii()
    ):
        return None
    if reverse:
        n = len(value)
        return value[n - stop : n - start]
    return value[start:stop]


_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_HOST_LABEL = _re(_LABEL)
_HOST_LABELS = _re(rf"{_LABEL}(?:\.{_LABEL})*")


def _is_valid_host_label(value: str | None, allow_sub_domains: bool) -> bool | None:
    if value is None:
        return None
    matcher = _HOST_LABELS if allow_sub_domains else _HOST_LABEL
    return matcher.fullmatch(value) is not None


# The rules library's IPv4 heuristic: four dot-separated groups of one to three
# digits without leading zeros.
_IPV4 = _re(r"(?:[0-9]|[1-9][0-9]{1,2})(?:\.(?:[0-9]|[1-9][0-9]{1,2})){3}")

# Characters a URI authority can't hold, which Smithy's reference rejects too.
_INVALID_AUTHORITY = _re(r'[\x00-\x20"<>\\^`{|}\x7f]')


def _is_ip_address(host: str) -> bool:
    if host.startswith("[") and host.endswith("]") and len(host) > 1:
        return True
    return _IPV4.fullmatch(host) is not None


def _parse_url(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parts = urlsplit(value)
        # Accessing port validates it.
        _ = parts.port
    except ValueError:
        return None
    # The authority is the host and port: the specification drops any userinfo.
    authority = parts.netloc.rpartition("@")[2]
    # Any query rejects the URL, even an empty one, which urlsplit doesn't report.
    has_query = "?" in value.partition("#")[0]
    if (
        parts.scheme not in ("http", "https")
        or has_query
        or not authority
        or _INVALID_AUTHORITY.search(parts.netloc)
    ):
        return None
    host = authority
    if not host.startswith("["):
        host = host.partition(":")[0]
    elif "]" in host:
        host = host[: host.index("]") + 1]
    path = parts.path
    if not path.strip():
        normalized = "/"
    else:
        normalized = path if path.startswith("/") else "/" + path
        if not normalized.endswith("/"):
            normalized += "/"
    return {
        "scheme": parts.scheme,
        "authority": authority,
        "path": path,
        "normalizedPath": normalized,
        "isIp": _is_ip_address(host),
    }


def _uri_encode(value: str | None) -> str | None:
    if value is None:
        return None
    return quote(value, safe="")


def _split(value: str | None, delimiter: str, limit: int) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not delimiter:
        raise ValueError("split delimiter must not be empty")
    if limit < 0:
        raise ValueError(f"split limit must not be negative: {limit}")
    if limit == 0:
        return tuple(value.split(delimiter))
    return tuple(value.split(delimiter, limit - 1))


STANDARD_FUNCTIONS: Mapping[str, Callable[..., Any]] = MappingProxyType(
    {
        "substring": _substring,
        "isValidHostLabel": _is_valid_host_label,
        "parseURL": _parse_url,
        "uriEncode": _uri_encode,
        "split": _split,
    }
)
"""The standard functions the engine calls, by rules-language name."""
