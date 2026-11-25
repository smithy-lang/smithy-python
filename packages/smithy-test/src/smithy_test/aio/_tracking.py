#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from collections.abc import Callable
from typing import Any

from .._private.http_mock import CURRENT_OPERATION, operation_name


def track_operation(invoke: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap an async ``_invoke`` so transports can tell which operation is called."""

    async def _invoke(*args: Any, **kwargs: Any) -> Any:
        token = CURRENT_OPERATION.set(operation_name(invoke, args, kwargs))
        try:
            return await invoke(*args, **kwargs)
        finally:
            CURRENT_OPERATION.reset(token)

    return _invoke
