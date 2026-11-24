#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.exceptions import SmithyError


class HTTPRecordError(SmithyError):
    """Raised when a call can't be recorded."""
