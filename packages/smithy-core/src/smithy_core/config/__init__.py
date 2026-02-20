# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.config import ConfigSource

from .resolver import ConfigResolver

__all__ = [
    "ConfigResolver",
    "ConfigSource",
]
