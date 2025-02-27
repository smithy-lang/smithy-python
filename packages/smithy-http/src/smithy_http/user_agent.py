#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportMissingTypeStubs=false,reportUnknownMemberType=false

from dataclasses import dataclass, field
from string import ascii_letters, digits

_USERAGENT_ALLOWED_CHARACTERS = ascii_letters + digits + "!$%&'*+-.^_`|~"


@dataclass(frozen=True, slots=True)
class UserAgentComponent:
    """Component of a User-Agent header string in the standard format.

    Each component consists of a prefix, a name, and a value. In the string
    representation these are combined in the format ``prefix/name#value``.

    This class is considered private and is subject to abrupt breaking changes.
    """

    prefix: str
    name: str
    value: str | None = None

    def __str__(self):
        """Create string like 'prefix/name#value' from a UserAgentComponent."""
        clean_prefix = sanitize_user_agent_string_component(
            self.prefix, allow_hash=True
        )
        clean_name = sanitize_user_agent_string_component(self.name, allow_hash=False)
        if self.value is None or self.value == "":
            return f"{clean_prefix}/{clean_name}"
        clean_value = sanitize_user_agent_string_component(self.value, allow_hash=True)
        return f"{clean_prefix}/{clean_name}#{clean_value}"


@dataclass(frozen=True, slots=True)
class RawStringUserAgentComponent:
    """UserAgentComponent interface wrapper around ``str``.

    Use for User-Agent header components that are not constructed from prefix+name+value
    but instead are provided as strings. No sanitization is performed.
    """

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(kw_only=True, slots=True)
class UserAgent:
    sdk_metadata: list[UserAgentComponent] = field(default_factory=list)
    internal_metadata: list[UserAgentComponent] = field(default_factory=list)
    ua_metadata: list[UserAgentComponent] = field(default_factory=list)
    api_metadata: list[UserAgentComponent] = field(default_factory=list)
    os_metadata: list[UserAgentComponent] = field(default_factory=list)
    language_metadata: list[UserAgentComponent] = field(default_factory=list)
    env_metadata: list[UserAgentComponent] = field(default_factory=list)
    config_metadata: list[UserAgentComponent] = field(default_factory=list)
    feat_metadata: list[UserAgentComponent] = field(default_factory=list)
    additional_metadata: list[UserAgentComponent | RawStringUserAgentComponent] = field(
        default_factory=list
    )

    def __str__(self) -> str:
        components = [
            *self.sdk_metadata,
            *self.internal_metadata,
            *self.ua_metadata,
            *self.api_metadata,
            *self.os_metadata,
            *self.language_metadata,
            *self.env_metadata,
            *self.config_metadata,
            *self.feat_metadata,
            *self.additional_metadata,
        ]
        return " ".join([str(comp) for comp in components])


def sanitize_user_agent_string_component(raw_str: str, allow_hash: bool = False) -> str:
    """Replaces all not allowed characters in the string with a dash ("-").

    Allowed characters are ASCII alphanumerics and ``!$%&'*+-.^_`|~``. If
    ``allow_hash`` is ``True``, "#"``" is also allowed.

    :type raw_str: str
    :param raw_str: The input string to be sanitized.

    :type allow_hash: bool
    :param allow_hash: Whether "#" is considered an allowed character.
    """
    return "".join(
        c if c in _USERAGENT_ALLOWED_CHARACTERS or (allow_hash and c == "#") else "-"
        for c in raw_str
    )
