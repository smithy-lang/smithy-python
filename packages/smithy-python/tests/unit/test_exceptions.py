# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from smithy_python.exceptions import (
    CodegenError,
    InvalidInvocationError,
    SmithyPythonError,
)


def test_error_hierarchy_distinguishes_invocation_and_codegen_failures() -> None:
    assert issubclass(CodegenError, SmithyPythonError)
    assert issubclass(InvalidInvocationError, SmithyPythonError)
    assert not issubclass(InvalidInvocationError, CodegenError)
