# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class AWSSDKWarning(UserWarning): ...


class BaseAWSSDKException(Exception):
    """Top-level exception to capture SDK-related errors."""


class MissingExpectedParameterException(BaseAWSSDKException, ValueError):
    """Some APIs require specific signing properties to be present."""
