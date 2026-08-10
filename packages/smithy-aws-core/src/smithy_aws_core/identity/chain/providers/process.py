#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import shlex
import sys

from smithy_core.exceptions import SmithyError
from smithy_core.interfaces.identity import Identity

from ...components import AWSCredentialsIdentity
from ...process import ProcessCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_CREDENTIAL_PROCESS = "credential_process"
_ACCOUNT_ID = "aws_account_id"


class ProcessConfigurationError(SmithyError):
    """Raised when a profile's credential process command is misconfigured."""


def _split_process_command(
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


class ProfileCredentialProcessProvider:
    """Adds a process credential resolver configured by the active profile."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.PROFILE_CREDENTIAL_PROCESS.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.PROFILE_CREDENTIAL_PROCESS)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver when the active profile configures a credential process."""
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        profile_name = setup.profile_name
        if config_file is None or profile_name is None:
            return

        command = config_file.get(profile_name, _CREDENTIAL_PROCESS)
        if not command:
            return

        # The process output's AccountId takes precedence; the profile's
        # aws_account_id is only used as a fallback.
        setup.add_terminal_resolver(
            ProcessCredentialsResolver(
                _split_process_command(command),
                account_id=config_file.get(profile_name, _ACCOUNT_ID),
            )
        )
