#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.exceptions import SmithyError

__all__ = ["SmithyHTTPError"]


class SmithyHTTPError(SmithyError):
    """Base exception type for all exceptions raised in HTTP clients."""
