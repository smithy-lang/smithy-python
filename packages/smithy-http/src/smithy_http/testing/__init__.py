# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Shared utilities for smithy-python functional tests."""

from .mockhttp import MockHTTPClient, MockHTTPClientError
from .utils import create_test_request

__version__ = "0.0.0"

__all__ = (
    "MockHTTPClient",
    "MockHTTPClientError",
    "create_test_request",
)
