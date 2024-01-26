#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Literal, Protocol


class HasFault(Protocol):
    """A protocol for a modeled error.
    All modeled errors will have a fault that is either "client" or "server".
    """

    fault: Literal["client", "server"]
