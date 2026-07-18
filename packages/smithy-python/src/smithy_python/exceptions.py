# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class CodegenError(Exception):
    """Base error raised for an invalid code generation request."""


class ModelError(CodegenError):
    """Raised when a Smithy JSON AST model is invalid or unsupported."""


class PluginError(CodegenError):
    """Raised when generator plugins cannot be loaded or ordered."""
