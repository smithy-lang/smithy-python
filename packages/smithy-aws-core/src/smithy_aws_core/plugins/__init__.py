#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Service-level client plugins for AWS clients."""

from typing import Protocol

from smithy_core.aio.interfaces.retries import RetryStrategy
from smithy_core.aio.retries import StandardRetryStrategy
from smithy_core.retries import RetryStrategyOptions

# DynamoDB uses max_attempts 4 and 25ms non-throttling backoff.
_DYNAMODB_DEFAULT_MAX_ATTEMPTS = 4
_DYNAMODB_DEFAULT_BACKOFF_SCALE = 0.025


class _RetryConfig(Protocol):
    retry_strategy: RetryStrategy | RetryStrategyOptions | None


def dynamodb_retry_plugin(config: _RetryConfig) -> None:
    """Apply DynamoDB's standard-mode retry defaults for any option left unset."""
    rs = config.retry_strategy
    if rs is not None and not isinstance(rs, RetryStrategyOptions):
        return
    if rs is not None and rs.retry_mode != "standard":
        return

    max_attempts = (
        rs.max_attempts
        if rs is not None and rs.max_attempts is not None
        else _DYNAMODB_DEFAULT_MAX_ATTEMPTS
    )
    config.retry_strategy = StandardRetryStrategy(
        max_attempts=max_attempts,
        default_backoff_scale=_DYNAMODB_DEFAULT_BACKOFF_SCALE,
    )
