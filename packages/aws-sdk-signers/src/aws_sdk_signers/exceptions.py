# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__all__ = (
    "AWSSDKWarning",
    "BaseAWSSDKException",
    "MissingExpectedParameterException",
    "ResourceLifecycleError",
)


class AWSSDKWarning(UserWarning):
    """Base category for warnings the SDK emits."""


class BaseAWSSDKException(Exception):
    """Top-level exception to capture SDK-related errors."""


class MissingExpectedParameterException(BaseAWSSDKException, ValueError):
    """Some APIs require specific signing properties to be present."""


class ResourceLifecycleError(BaseAWSSDKException, RuntimeError):
    """A resource was used after it was closed or finalized."""
