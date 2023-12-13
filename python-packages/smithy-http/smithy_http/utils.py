#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from urllib.parse import quote as urlquote

from smithy_core.exceptions import SmithyException


def split_header(given: str, handle_unquoted_http_date: bool = False) -> list[str]:
    """Splits a header value into a list of strings.

    The format is based on RFC9110's list production found in secion 5.6.1 with
    the quoted string production found in section 5.6.4. In short:

    A list is 1 or more elements surrounded by optional whitespace and separated by
    commas. Elements may be quoted with double quotes (``"``) to contain leading or
    trailing whitespace, commas, or double quotes. Inside the the double quotes, a
    value may be escaped with a backslash (``\\``). Elements that contain no contents
    are ignored.

    If the list is known to contain unquoted IMF-fixdate formatted timestamps, the
    ``handle_unquoted_http_date`` parameter can be set to ensure the list isn't
    split on the commas inside the timestamps.

    :param given: The header value to split.
    :param handle_unquoted_http_date: Support splitting IMF-fixdate lists without
        quotes. Defaults to False.
    :returns: The header value split on commas.
    """
    result: list[str] = []

    i = 0
    while i < len(given):
        if given[i].isspace():
            # Skip any leading space.
            i += 1
        elif given[i] == '"':
            # Grab the contents of the quoted value and append it.
            entry, i = _consume_until(given, i + 1, '"', escape_char="\\")
            result.append(entry)

            if i > len(given) or given[i - 1] != '"':
                raise SmithyException(
                    f"Invalid header list syntax: expected end quote but reached end "
                    f"of value: `{given}`"
                )

            # Skip until the next comma.
            excess, i = _consume_until(given, i, ",")
            if excess.strip():
                raise SmithyException(
                    f"Invalid header list syntax: Found quote contents after "
                    f"end-quote: `{excess}` in `{given}`"
                )
        else:
            entry, i = _consume_until(
                given, i, ",", skip_first=handle_unquoted_http_date
            )
            if stripped := entry.strip():
                result.append(stripped)

    return result


def _consume_until(
    given: str,
    start_index: int,
    end_char: str,
    escape_char: str | None = None,
    skip_first: bool = False,
) -> tuple[str, int]:
    """Creates a slice of the given string from the start index to the end character.

    This also handles resolving escaped characters using the given escape_char if
    provided.

    If `skip_first` is true, the first instance of the end character will be skipped.
    This is to enable support for unquoted IMF fixdate timestamps.

    :param given: The whole header string.
    :param start_index: The index at which to start slicing.
    :param end_char: The character to split on. This is not included in the output.
    :param escape_char: The character to escape with, e.g. ``\\``.
    :param skip_first: Whether to skip the first instance of the end character.
    :returns: A substring from the start index to the first instance of the end char.
    """
    should_skip = skip_first
    end_index = start_index
    result = ""
    escaped = False
    while end_index < len(given):
        if escaped:
            result += given[end_index]
            escaped = False
        elif given[end_index] == escape_char:
            escaped = True
        elif given[end_index] == end_char:
            if should_skip:
                result += given[end_index]
                should_skip = False
            else:
                break
        else:
            result += given[end_index]
        end_index += 1
    return result, end_index + 1


def join_query_params(params: list[tuple[str, str | None]], prefix: str = "") -> str:
    """Join a list of query parameter key-value tuples.

    :param params: The list of key-value query parameter tuples.
    :param prefix: An optional query prefix.
    """
    query: str = prefix
    for param in params:
        if query:
            query += "&"
        if param[1] is None:
            query += urlquote(param[0], safe="")
        else:
            query += f"{urlquote(param[0], safe='')}={urlquote(param[1], safe='')}"
    return query
