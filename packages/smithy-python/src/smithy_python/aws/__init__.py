# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Client generation for AWS services, as integrations of the core generator.

A service with the ``aws.api#service`` trait gets clients named for its SDK ID and
configs that resolve from the environment and shared config files. Its clients also
send the AWS user agent. A service with the ``aws.auth#sigv4`` trait also gets SigV4
auth and the default AWS credentials chain, and one with ``smithy.api#httpBearerAuth``
gets bearer auth and the default AWS token provider chain. AWS services, and
services whose rules use AWS functions or built-ins, resolve endpoints with the
AWS rules extension.
Clients may also use the AWS protocols ``aws.protocols#restJson1``,
``awsJson1_0``, ``awsJson1_1``, ``restXml``, ``awsQuery`` and ``ec2Query``.
"""

from __future__ import annotations

from typing import Final

from ._checksums import AwsChecksumsIntegration
from ._config import AwsConfigIntegration
from ._dependencies import SMITHY_AWS_CORE
from ._endpoints import AwsEndpointsIntegration
from ._identity import AwsIdentityIntegration
from ._protocols import (
    AWS_JSON_10,
    AWS_JSON_11,
    AWS_PROTOCOLS,
    AWS_QUERY,
    EC2_QUERY,
    REST_JSON,
    REST_XML,
)

__all__ = [
    "AWS_INTEGRATIONS",
    "AWS_JSON_10",
    "AWS_JSON_11",
    "AWS_PROTOCOLS",
    "AWS_QUERY",
    "EC2_QUERY",
    "REST_JSON",
    "REST_XML",
    "SMITHY_AWS_CORE",
    "AwsChecksumsIntegration",
    "AwsConfigIntegration",
    "AwsEndpointsIntegration",
    "AwsIdentityIntegration",
]

AWS_INTEGRATIONS: Final = (
    AwsConfigIntegration(),
    AwsIdentityIntegration(),
    AwsEndpointsIntegration(),
    AwsChecksumsIntegration(),
)
"""The integrations AWS services get, in order."""
