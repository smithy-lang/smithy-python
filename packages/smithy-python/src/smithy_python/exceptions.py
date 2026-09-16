# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Exceptions raised by Smithy Python code generation."""


class SmithyPythonError(Exception):
    """Base exception for errors raised by the Smithy Python generator."""


class CodegenError(SmithyPythonError):
    """Raised when code generation fails."""


class InvalidInvocationError(SmithyPythonError):
    """Raised when command-line inputs do not form a valid invocation."""
