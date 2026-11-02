# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace
from typing import Any

import pytest
from smithy_aws_core.endpoints import AWS_RULES_EXTENSION
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.auth import RESOLVED_IDENTITY
from smithy_core.endpoints import (
    BddEndpointResolver,
    EndpointBdd,
    EndpointResolverParams,
)
from smithy_core.endpoints._types import Tag
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType
from smithy_core.types import TypedProperties

FUNCTIONS = AWS_RULES_EXTENSION.functions


@pytest.mark.parametrize(
    "region, name, dns",
    [
        ("us-east-1", "aws", "amazonaws.com"),
        ("us-gov-west-1", "aws-us-gov", "amazonaws.com"),
        ("cn-north-1", "aws-cn", "amazonaws.com.cn"),
        ("us-iso-east-1", "aws-iso", "c2s.ic.gov"),
        ("eusc-de-east-1", "aws-eusc", "amazonaws.eu"),
        # Known regions match before the region patterns.
        ("aws-us-gov-global", "aws-us-gov", "amazonaws.com"),
        # A region no pattern matches is in the aws partition.
        ("mars-east-1", "aws", "amazonaws.com"),
        # Unknown regions that match a partition's region pattern.
        ("us-east-99", "aws", "amazonaws.com"),
        ("us-gov-east-9", "aws-us-gov", "amazonaws.com"),
        ("cn-north-9", "aws-cn", "amazonaws.com.cn"),
    ],
)
def test_partition(region: str, name: str, dns: str) -> None:
    partition = FUNCTIONS["aws.partition"](region)
    assert partition["name"] == name
    assert partition["dnsSuffix"] == dns


def test_known_regions_merge_their_properties() -> None:
    partition = AWS_RULES_EXTENSION.functions["aws.partition"]("af-south-1")
    assert partition["dnsSuffix"] == "amazonaws.com"
    assert partition["description"] == "Africa (Cape Town)"


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            "arn:aws:s3:us-west-2:123456789012:accesspoint/myendpoint",
            {
                "partition": "aws",
                "service": "s3",
                "region": "us-west-2",
                "accountId": "123456789012",
                "resourceId": ("accesspoint", "myendpoint"),
            },
        ),
        (
            "arn:aws:s3-outposts:us-west-2:123:outpost:op-01:accesspoint:ap",
            {
                "partition": "aws",
                "service": "s3-outposts",
                "region": "us-west-2",
                "accountId": "123",
                "resourceId": ("outpost", "op-01", "accesspoint", "ap"),
            },
        ),
        (
            "arn:aws:iam::123456789012:user/a/b",
            {
                "partition": "aws",
                "service": "iam",
                "region": "",
                "accountId": "123456789012",
                "resourceId": ("user", "a", "b"),
            },
        ),
        ("arn:aws:s3:us-west-2:123456789012:", None),
        ("arn:aws:s3:us-west-2", None),
        ("bucket", None),
    ],
)
def test_parse_arn(value: str, expected: dict[str, Any] | None) -> None:
    assert FUNCTIONS["aws.parseArn"](value) == expected


@pytest.mark.parametrize(
    "value, allow_sub_domains, expected",
    [
        ("my-bucket-1", False, True),
        ("ab", False, False),
        ("a" * 64, False, False),
        ("Bucket", False, False),
        ("-bucket", False, False),
        ("my.bucket", False, False),
        ("my.bucket", True, True),
        ("my..bucket", True, False),
        ("192.168.5.4", True, False),
    ],
)
def test_is_virtual_hostable_s3_bucket(
    value: str, allow_sub_domains: bool, expected: bool
) -> None:
    assert FUNCTIONS["aws.isVirtualHostableS3Bucket"](value, allow_sub_domains) is (
        expected
    )


# --------------------------------------------------------------- built-ins

# Each AWS built-in, and one that is also a client context parameter.
PARAMETERS: tuple[tuple[Any, ...], ...] = (
    ("Region", "string", False, None, "AWS::Region", False),
    ("UseFIPS", "boolean", True, False, "AWS::UseFIPS", False),
    ("UseDualStack", "boolean", True, False, "AWS::UseDualStack", False),
    ("Mode", "string", False, None, "AWS::Auth::AccountIdEndpointMode", False),
    ("AccountId", "string", False, None, "AWS::Auth::AccountId", False),
    ("StsGlobal", "boolean", True, False, "AWS::STS::UseGlobalEndpoint", False),
    ("S3Global", "boolean", True, False, "AWS::S3::UseGlobalEndpoint", False),
    ("ForcePathStyle", "boolean", False, None, "AWS::S3::ForcePathStyle", True),
)
NAMES = tuple(name for name, *_ in PARAMETERS)
# One endpoint, with each parameter's value as a property of its name.
BDD = EndpointBdd(
    parameters=PARAMETERS,
    functions=(),
    conditions=(),
    results=(
        None,
        (
            Tag.ENDPOINT,
            "https://example.com",
            (Tag.MAP, NAMES, *((Tag.REF, name) for name in NAMES)),
            (),
        ),
    ),
    root=100_000_001,
    nodes=(-1, 1, -1),
)
OPERATION: APIOperation[Any, Any] = APIOperation(
    static_schema=(
        ShapeType.OPERATION.value,
        "com.example",
        "Op",
        0,
        (ShapeType.STRUCTURE.value, "com.example", "OpInput", 0, (), ()),
        -1,
        (),
    ),
)


def _bound(config: Any, identity: Any = None) -> dict[str, Any]:
    """The parameter values a call binds, by name."""
    context = TypedProperties({"config": config})
    if identity is not None:
        context[RESOLVED_IDENTITY] = identity
    resolver = BddEndpointResolver(BDD, extensions=[AWS_RULES_EXTENSION])
    endpoint = resolver.resolve_endpoint(
        EndpointResolverParams(operation=OPERATION, input=None, context=context)
    )
    return dict(endpoint.properties.items())


def test_builtins_read_their_sources() -> None:
    config = SimpleNamespace(
        endpoint_uri=None,
        region="us-west-2",
        use_fips_endpoint=True,
        use_dualstack_endpoint=True,
        account_id_endpoint_mode="disabled",
        force_path_style=True,
    )
    identity = AWSCredentialsIdentity(
        access_key_id="AKID", secret_access_key="SECRET", account_id="111122223333"
    )
    assert _bound(config, identity) == {
        "Region": "us-west-2",
        "UseFIPS": True,
        "UseDualStack": True,
        "Mode": "disabled",
        "AccountId": "111122223333",
        # Not bound: they select legacy global endpoints.
        "StsGlobal": False,
        "S3Global": False,
        "ForcePathStyle": True,
    }


def test_unset_builtins_take_their_defaults() -> None:
    identity = AWSCredentialsIdentity(access_key_id="AKID", secret_access_key="SECRET")
    assert _bound(SimpleNamespace(endpoint_uri=None), identity) == {
        "Region": None,
        "UseFIPS": False,
        "UseDualStack": False,
        "Mode": None,
        "AccountId": None,
        "StsGlobal": False,
        "S3Global": False,
        "ForcePathStyle": None,
    }
