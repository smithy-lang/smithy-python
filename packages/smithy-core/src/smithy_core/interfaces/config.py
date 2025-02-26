#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Protocol, Any

from smithy_core.interceptors import Interceptor
from smithy_core.interfaces.retries import RetryStrategy


class Config(Protocol):
    interceptors: list[Interceptor[Any, Any, Any, Any]]
    retry_strategy: RetryStrategy
