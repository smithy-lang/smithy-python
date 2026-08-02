#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import shlex
import sys

from smithy_core.interfaces.identity import Identity

from ...components import AWSCredentialsIdentity
from ...process import ProcessCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_CREDENTIAL_PROCESS = "credential_process"


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
    return shlex.split(command)


def _split_windows_command(command: str) -> list[str]:
    """Split a command using the Microsoft C runtime argument parsing rules."""
    arguments: list[str] = []
    argument: list[str] = []
    argument_started = False
    in_quotes = False
    backslashes = 0

    for character in command:
        if character == "\\":
            backslashes += 1
            argument_started = True
            continue

        if character == '"':
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
            argument.extend("\\" * backslashes)
            backslashes = 0

        if character in (" ", "\t") and not in_quotes:
            if argument_started:
                arguments.append("".join(argument))
                argument = []
                argument_started = False
            continue

        argument.append(character)
        argument_started = True

    if in_quotes:
        raise ValueError(f"No closing quotation in string: {command}")

    if backslashes:
        argument.extend("\\" * backslashes)
    if argument_started:
        arguments.append("".join(argument))

    return arguments


class ProfileProcessCredentialsProvider:
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

        setup.add_terminal_resolver(
            ProcessCredentialsResolver(_split_process_command(command))
        )
