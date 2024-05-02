#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import NamedTuple

from smithy_core.documents import DocumentValue

_REST_JSON_CODE_HEADER = "x-amzn-errortype"

_REST_JSON_CODE_KEYS = {"__type", "code"}

_REST_JSON_MESSAGE_KEYS = {"message", "errormessage", "error_message"}


class RestJsonErrorInfo(NamedTuple):
    """Generic error information from a RestJson protocol error."""

    code: str
    """The error code."""

    message: str
    """The generic error message.

    A modeled error may have the error bound somewhere else. This is based off of
    checking the most common locations and is intended for use with excpetions that
    either didn't model the message or which are unknown.
    """

    json_body: dict[str, DocumentValue] | None = None
    """The HTTP response body parsed as JSON."""
