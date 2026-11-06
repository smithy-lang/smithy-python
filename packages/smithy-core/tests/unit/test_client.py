#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, cast
from unittest.mock import Mock

from smithy_core.client import Client
from smithy_core.retries import RETRY_STRATEGY, StandardRetryStrategy


def test_build_call_adds_retry_strategy_to_request_properties() -> None:
    retry_strategy = StandardRetryStrategy()
    _, call = Client()._build_call(  # pyright: ignore[reportPrivateUsage]
        cast(Any, Mock()),
        cast(Any, Mock()),
        config=Mock(interceptors=[]),
        retry_strategy=retry_strategy,
    )

    assert call.context[RETRY_STRATEGY] is retry_strategy
    assert call.retry_strategy is retry_strategy
