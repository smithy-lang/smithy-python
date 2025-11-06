#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.identity import StaticCredentialsResolver
from smithy_http.testing import MockHTTPClient

from ..codegen.aws_kitchen_sink.client import AwsKitchenSink
from ..codegen.aws_kitchen_sink.config import Config


@pytest.fixture
def http_client() -> MockHTTPClient:
    return MockHTTPClient()


@pytest.fixture
def client(http_client: MockHTTPClient) -> AwsKitchenSink:
    config = Config(
        transport=http_client,
        endpoint_uri="https://test.aws.dev",
        aws_access_key_id="fake-access-key",
        aws_secret_access_key="fake-secret-key",
        aws_credentials_identity_resolver=StaticCredentialsResolver(),
        region="us-west-2",
    )
    return AwsKitchenSink(config=config)
