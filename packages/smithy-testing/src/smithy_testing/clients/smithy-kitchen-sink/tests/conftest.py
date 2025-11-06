#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_http.testing import MockHTTPClient

from ..codegen.smithy_kitchen_sink.client import SmithyKitchenSink
from ..codegen.smithy_kitchen_sink.config import Config


@pytest.fixture
def http_client() -> MockHTTPClient:
    return MockHTTPClient()


@pytest.fixture
def client(http_client: MockHTTPClient) -> SmithyKitchenSink:
    config = Config(
        transport=http_client,
        endpoint_uri="https://test.smithy.dev",
    )
    return SmithyKitchenSink(config=config)
