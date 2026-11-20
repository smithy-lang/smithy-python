# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Client generation for AWS services, as integrations of the core generator.

A service with the ``aws.api#service`` trait gets clients named for its SDK ID and
configs that resolve from the environment and shared config files. Its clients also
send the AWS user agent. A service with the ``aws.auth#sigv4`` trait also gets SigV4
auth and the default AWS credentials chain.
"""

from __future__ import annotations

from typing import Final

from ._config import AwsConfigIntegration
from ._dependencies import SMITHY_AWS_CORE
from ._sigv4 import AwsSigV4Integration

__all__ = [
    "AWS_INTEGRATIONS",
    "SMITHY_AWS_CORE",
    "AwsConfigIntegration",
    "AwsSigV4Integration",
]

AWS_INTEGRATIONS: Final = (AwsConfigIntegration(), AwsSigV4Integration())
"""The integrations AWS services get, in order."""
