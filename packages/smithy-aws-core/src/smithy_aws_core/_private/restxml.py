#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import NamedTuple
from xml.etree.ElementTree import ParseError, fromstring

from .query._xml import find_child, local_name


class RestXmlErrorInfo(NamedTuple):
    code: str | None
    """The error's ``Code``."""

    message: str | None
    """The error's ``Message``.

    Some models name the member ``message`` while services send ``<Message>``, so this
    is the fallback when the modeled member isn't populated.
    """

    wrapper_elements: tuple[str, ...]
    """The elements enclosing the error's members."""


def parse_rest_xml_error(body: bytes) -> RestXmlErrorInfo:
    """Parse the code, message, and wrapper elements of a restXml error response.

    Errors are normally wrapped as ``<ErrorResponse><Error>...</Error></ErrorResponse>``,
    but services with ``noErrorWrapping`` (such as S3) send a bare ``<Error>``. Both are
    accepted so the protocol needn't be configured for either.
    """
    try:
        element = fromstring(body)  # noqa: S314
    except ParseError:
        return _EMPTY

    wrapper_elements: tuple[str, ...] = ("Error",)
    if local_name(element.tag) == "ErrorResponse":
        error = find_child(element, "Error")
        if error is None:
            return _EMPTY
        element = error
        wrapper_elements = ("ErrorResponse", "Error")
    elif local_name(element.tag) != "Error":
        return _EMPTY

    code = find_child(element, "Code")
    message = find_child(element, "Message")
    return RestXmlErrorInfo(
        code=code.text if code is not None else None,
        message=message.text if message is not None else None,
        wrapper_elements=wrapper_elements,
    )


_EMPTY = RestXmlErrorInfo(None, None, ())
