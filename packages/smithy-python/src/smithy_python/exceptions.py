# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Exceptions raised by Smithy Python code generation."""


class SmithyPythonError(Exception):
    """Base exception for errors raised by the Smithy Python generator."""


class CodegenError(SmithyPythonError):
    """Raised when code generation fails."""


class InvalidInvocationError(SmithyPythonError):
    """Raised when command-line inputs do not form a valid invocation."""


class ModelError(CodegenError):
    """Raised when a Smithy model cannot be loaded or navigated."""


class InvalidShapeIdError(ModelError, ValueError):
    """Raised when a string is not a valid Smithy shape ID."""


class ShapeNotFoundError(ModelError, LookupError):
    """Raised when a shape ID does not resolve to a shape in the model."""
