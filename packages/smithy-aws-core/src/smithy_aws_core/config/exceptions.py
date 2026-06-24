# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Config related exceptions"""


class ConfigParseError(Exception):
    """Raised when a config file cannot be parsed due to invalid syntax."""
