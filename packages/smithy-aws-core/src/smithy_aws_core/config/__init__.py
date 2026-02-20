# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from .resolver import get_shared_resolver, reset_shared_resolver
from .sources import EnvironmentSource

__all__ = [
    "EnvironmentSource",
    "get_shared_resolver",
    "reset_shared_resolver",
]
