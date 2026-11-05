#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The AWS endpoint rules library: AWS functions, built-in parameter bindings and auth
schemes."""

import json
import os
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from smithy_core.aio.client import AUTH_SCHEME
from smithy_core.auth import RESOLVED_IDENTITY
from smithy_core.endpoints import EndpointAuthScheme, RulesExtension
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.shapes import ShapeID
from smithy_core.types import TypedProperties

from ..traits import SigV4Trait


def _build_partitions(
    partitions: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    tuple[tuple[re.Pattern[str], dict[str, Any]], ...],
    dict[str, Any] | None,
]:
    """Index the partitions: known regions, region patterns, and the aws partition.

    A known region's record is its partition's outputs merged with the region's own
    properties.
    """
    by_region: dict[str, dict[str, Any]] = {}
    patterns: list[tuple[re.Pattern[str], dict[str, Any]]] = []
    default = None
    for partition in partitions:
        record = partition["outputs"]
        for region, properties in partition["regions"].items():
            by_region.setdefault(region, {**record, **properties})
        patterns.append((re.compile(partition["regionRegex"], re.ASCII), record))
        if partition["id"] == "aws":
            default = record
    return by_region, tuple(patterns), default


def _load_partitions() -> list[dict[str, Any]]:
    # partitions.json is the release pipeline's partitions artifact, byte for byte.
    # The pipeline replaces it when the artifact changes, so don't edit it by hand.
    with open(os.path.join(os.path.dirname(__file__), "partitions.json"), "rb") as file:
        return json.load(file)["partitions"]


_BY_REGION, _PATTERNS, _DEFAULT_PARTITION = _build_partitions(_load_partitions())
_PARTITION_CACHE: dict[str, dict[str, Any] | None] = {}
_PARTITION_CACHE_SIZE = 512


def _partition(region: str | None) -> dict[str, Any] | None:
    """``aws.partition``: the partition of a region, memoized per region.

    Known regions come first, then the first partition whose region pattern
    matches, then the ``aws`` partition. The returned record is shared and must not
    be mutated.
    """
    if region is None:
        return None
    try:
        return _PARTITION_CACHE[region]
    except KeyError:
        pass
    record = _BY_REGION.get(region)
    if record is None:
        for pattern, candidate in _PATTERNS:
            if pattern.fullmatch(region):
                record = candidate
                break
        else:
            record = _DEFAULT_PARTITION
    if len(_PARTITION_CACHE) < _PARTITION_CACHE_SIZE:
        _PARTITION_CACHE[region] = record
    return record


_ARN_RESOURCE_SEPARATOR = re.compile(r"[:/]")


def _parse_arn(value: str | None) -> dict[str, Any] | None:
    """``aws.parseArn``: the parts of an ARN, or None when it is not one."""
    if value is None or len(value) < 8 or not value.startswith("arn:"):
        return None
    parts = value.split(":", 5)
    if len(parts) != 6:
        return None
    _, partition, service, region, account_id, resource = parts
    if not partition or not service or not resource:
        return None
    return {
        "partition": partition,
        "service": service,
        "region": region,
        "accountId": account_id,
        "resourceId": tuple(_ARN_RESOURCE_SEPARATOR.split(resource)),
    }


_BUCKET = re.compile(r"[a-z0-9][a-z0-9-]*[a-z0-9]")
_DOTTED_BUCKET = re.compile(
    r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*"
)
# The rules library's IPv4 heuristic: four dot-separated groups of one to three
# digits without leading zeros.
_IPV4 = re.compile(r"(?:[0-9]|[1-9][0-9]{1,2})(?:\.(?:[0-9]|[1-9][0-9]{1,2})){3}")


def _is_virtual_hostable_s3_bucket(
    value: str | None, allow_sub_domains: bool
) -> bool | None:
    """``aws.isVirtualHostableS3Bucket``: whether a bucket can be a host label."""
    if value is None:
        return None
    if not 3 <= len(value) <= 63:
        return False
    if not allow_sub_domains:
        return _BUCKET.fullmatch(value) is not None
    return (
        _DOTTED_BUCKET.fullmatch(value) is not None and _IPV4.fullmatch(value) is None
    )


def _account_id(config: Any, context: _TypedProperties) -> str | None:
    """``AWS::Auth::AccountId``: the account ID of the identity resolved for the call."""
    return getattr(context.get(RESOLVED_IDENTITY), "account_id", None)


_NO_AUTH = ShapeID("smithy.api#noAuth")


def _account_id_endpoint_mode(config: Any, context: _TypedProperties) -> str | None:
    """``AWS::Auth::AccountIdEndpointMode``: the configured mode, or ``disabled`` when
    the request is unsigned."""
    scheme = context.get(AUTH_SCHEME)
    if scheme is None or scheme.scheme_id == _NO_AUTH:
        return "disabled"
    return getattr(config, "account_id_endpoint_mode", None)


_SIGV4A = ShapeID("aws.auth#sigv4a")
# Shape IDs can't hold "-".
_SIGV4_S3EXPRESS = ShapeID("aws.auth#sigv4S3express")


def _sigv4(entry: Mapping[str, Any]) -> EndpointAuthScheme:
    """The SigV4 endpoint auth scheme, with the entry's signing overrides."""
    data: dict[str, Any] = {}
    if (signing_name := entry.get("signingName")) is not None:
        data["service"] = signing_name
    if (signing_region := entry.get("signingRegion")) is not None:
        data["region"] = signing_region
    if (disable_double_encoding := entry.get("disableDoubleEncoding")) is not None:
        data["uri_encode_path"] = not disable_double_encoding
    if (disable_normalize_path := entry.get("disableNormalizePath")) is not None:
        data["normalize_path"] = not disable_normalize_path
    properties = TypedProperties()
    properties.data = data
    return EndpointAuthScheme(scheme_id=SigV4Trait.id, properties=properties)


def _sigv4a(entry: Mapping[str, Any]) -> EndpointAuthScheme:
    """The SigV4a endpoint auth scheme."""
    return EndpointAuthScheme(scheme_id=_SIGV4A)


def _sigv4_s3express(entry: Mapping[str, Any]) -> EndpointAuthScheme:
    """The S3 Express endpoint auth scheme."""
    return EndpointAuthScheme(scheme_id=_SIGV4_S3EXPRESS)


AWS_RULES_EXTENSION = RulesExtension(
    functions=MappingProxyType(
        {
            "aws.partition": _partition,
            "aws.parseArn": _parse_arn,
            "aws.isVirtualHostableS3Bucket": _is_virtual_hostable_s3_bucket,
        }
    ),
    builtins=MappingProxyType(
        {
            "AWS::Region": "region",
            "AWS::UseFIPS": "use_fips_endpoint",
            "AWS::UseDualStack": "use_dualstack_endpoint",
            "AWS::Auth::AccountIdEndpointMode": _account_id_endpoint_mode,
            "AWS::Auth::AccountId": _account_id,
        }
    ),
    auth_schemes=MappingProxyType(
        {
            "sigv4": _sigv4,
            "sigv4a": _sigv4a,
            "sigv4-s3express": _sigv4_s3express,
        }
    ),
)
"""AWS rules functions, built-in bindings and auth schemes."""
