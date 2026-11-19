# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Runtime dependencies of generated AWS clients."""

from __future__ import annotations

from typing import Final

from ..dependencies import Dependency

SMITHY_AWS_CORE: Final = Dependency(
    package="smithy-aws-core",
    specifier="~=0.16.0",
    group="runtime",
)
"""Compatible smithy-aws-core runtime for generated AWS clients.

CAUTION: Keep the specifier at the package's current minor version.
"""
