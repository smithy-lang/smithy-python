#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Protocol

from smithy_http.aio.interfaces import HTTPClient

from smithy_aws_core.identity import AWSCredentialsResolver


class AwsCredentialsConfig(Protocol):
    """Configuration required for resolving credentials."""

    http_client: HTTPClient


class CredentialsSource(Protocol):
    def is_available(self, config: AwsCredentialsConfig) -> bool:
        """Returns True if credentials are available from this source."""
        ...

    def build_resolver(self, config: AwsCredentialsConfig) -> AWSCredentialsResolver:
        """Builds a credentials resolver for the given configuration."""
        ...
