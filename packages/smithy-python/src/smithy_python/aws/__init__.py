# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Client generation for AWS services, as integrations of the core generator.

A service with the ``aws.api#service`` trait gets clients named for its SDK ID and
configs that resolve from the environment and shared config files. Its clients also
send the AWS user agent.
"""

from __future__ import annotations

from typing import Final

from ._config import AwsConfigIntegration
from ._dependencies import SMITHY_AWS_CORE

__all__ = ["AWS_INTEGRATIONS", "SMITHY_AWS_CORE", "AwsConfigIntegration"]

AWS_INTEGRATIONS: Final = (AwsConfigIntegration(),)
"""The integrations AWS services get, in order."""
