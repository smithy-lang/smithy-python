#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
class SmithyException(Exception):
    """Base exception type for all exceptions raised by smithy-python."""


class SmithyRetryException(SmithyException):
    """Base exception type for all exceptions raised in retry strategies."""


class ExpectationNotMetException(SmithyException):
    """Exception type for exceptions thrown by unmet assertions."""


class SmithyIdentityException(SmithyException):
    """Base exception type for all exceptions raised in identity resolution."""


class MissingDependencyException(SmithyException):
    """Exception type raised when a feature that requires a missing optional dependency
    is called."""
