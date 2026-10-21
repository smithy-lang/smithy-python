#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import shlex
import sys

from smithy_core.exceptions import SmithyError


class ProcessConfigurationError(SmithyError):
    """Raised when a profile's credential process command is misconfigured."""


def _split_process_command(  # type: ignore[reportUnusedFunction]
    command: str,
    *,
    platform: str | None = None,
) -> list[str]:
    """Split a process command according to the host platform's quoting rules."""
    if platform is None:
        platform = sys.platform
    if platform == "win32":
        return _split_windows_command(command)
    try:
        return shlex.split(command)
    except ValueError as e:
        raise ProcessConfigurationError(
            f"Could not parse credential process command: {e}"
        ) from e


def _split_windows_command(command: str) -> list[str]:
    """Split a command using botocore's strict form of the Microsoft C runtime rules.

    The underlying runtime rules are documented at:
    https://learn.microsoft.com/en-us/cpp/cpp/main-function-command-line-args#parsing-c-command-line-arguments
    """
    arguments: list[str] = []
    argument: list[str] = []
    argument_started = False
    in_quotes = False
    backslashes = 0

    for character in command:
        if character == "\\":
            # Delay emitting backslashes until we know whether a quote follows.
            backslashes += 1
            argument_started = True
            continue

        if character == '"':
            # Pairs become literal backslashes; an odd remainder escapes the quote.
            literal_backslashes, escaped_quote = divmod(backslashes, 2)
            argument.extend("\\" * literal_backslashes)
            backslashes = 0
            argument_started = True
            if escaped_quote:
                argument.append('"')
            else:
                in_quotes = not in_quotes
            continue

        if backslashes:
            # Without a following quote, backslashes are literal.
            argument.extend("\\" * backslashes)
            backslashes = 0

        # Only spaces and tabs outside quotes delimit Windows arguments.
        if character in (" ", "\t") and not in_quotes:
            # This preserves empty quoted arguments while ignoring extra whitespace.
            if argument_started:
                arguments.append("".join(argument))
                argument = []
                argument_started = False
            continue

        argument.append(character)
        argument_started = True

    if in_quotes:
        raise ProcessConfigurationError(f"No closing quotation in string: {command}")

    if backslashes:
        argument.extend("\\" * backslashes)
    if argument_started:
        arguments.append("".join(argument))

    return arguments
