#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.endpoints import StaticEndpointConfig
from smithy_core.types import PropertyKey


class RegionalEndpointConfig(StaticEndpointConfig):
    """Endpoint config for services with standard regional endpoints."""

    region: str | None
    """The AWS region to address the request to."""


REGIONAL_ENDPOINT_CONFIG = PropertyKey(key="config", value_type=RegionalEndpointConfig)
"""Endpoint config for services with standard regional endpoints."""
