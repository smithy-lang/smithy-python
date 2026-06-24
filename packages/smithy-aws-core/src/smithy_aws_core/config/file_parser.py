# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from smithy_aws_core.config.exceptions import ConfigParseError

# Type aliases
type PropertyValue = str | dict[str, str]
type ProfileProperties = dict[str, PropertyValue]
type ProfileMap = dict[str, ProfileProperties]
type RawParsedSections = dict[str, dict[str, str | dict[str, str]]]

_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_\-/.%@:+]+$")


class FileType(Enum):
    CONFIG = "config"
    CREDENTIALS = "credentials"


@dataclass
class StandardizedOutput:
    """Normalized output after standardization."""

    profiles: ProfileMap = field(default_factory=dict)  # type: ignore[assignment]
    sso_sessions: ProfileMap = field(default_factory=dict)  # type: ignore[assignment]
    services: ProfileMap = field(default_factory=dict)  # type: ignore[assignment]


async def parse_config_file(file_path: str) -> RawParsedSections:
    """Parse an AWS config or credentials file.

    Reads the file asynchronously and parses it into raw sections.

    :param file_path: Resolved path to the file.
    :returns: Raw sections dict {section_name: {key: value}}.
    :raises ConfigParseError: If the file has invalid syntax.
    """
    content = await _read_file(file_path)
    if content is None:
        return {}
    return parse_content(content)


def standardize(
    raw_sections: RawParsedSections, file_type: FileType
) -> StandardizedOutput:
    """Standardize raw parsed sections into a normalized profile map.

    Handles:
    - Stripping 'profile ' prefix (config files only)
    - [default] vs [profile default] precedence
    - Invalid profile/property name filtering
    - Duplicate profile merging
    - Separating profiles, sso-sessions, and services

    :param raw_sections: Raw sections from parse_config_file().
    :param file_type: Whether this is a config or credentials file.
    :returns: StandardizedOutput with profiles, sso_sessions, and services.
    """
    profiles: ProfileMap = {}
    sso_sessions: ProfileMap = {}
    services: ProfileMap = {}

    has_profile_default = False
    if file_type == FileType.CONFIG:
        has_profile_default = any(
            _is_profile_prefixed_default(name) for name in raw_sections
        )

    for section_name, properties in raw_sections.items():
        if file_type == FileType.CONFIG:
            _classify_config_section(
                section_name,
                properties,
                profiles,
                sso_sessions,
                services,
                has_profile_default,
            )
        else:
            _classify_credentials_section(
                section_name,
                properties,
                profiles,
            )

    return StandardizedOutput(
        profiles=profiles,
        sso_sessions=sso_sessions,
        services=services,
    )


async def _read_file(path: str) -> str | None:
    """Read file content asynchronously.

    Returns None if the file doesn't exist or can't be opened.
    Per the SEP: inaccessible files are treated as empty.
    """
    try:
        content = await asyncio.to_thread(Path(path).read_text, encoding="utf-8")
        return content
    except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
        return None


def parse_content(content: str) -> RawParsedSections:
    """Parse config file content from a string into raw sections.

    Note: This function is public only for direct use by unit tests
    In normal config loading, use parse_config_file() which handles file I/O and
    calls this internally.

    :param content: The raw config file content as a string.
    :returns: Raw sections dict {section_name: {key: value}}.
    :raises ConfigParseError: If the content has invalid syntax.
    """
    sections: RawParsedSections = {}
    current_section: str | None = None
    current_key: str | None = None
    in_sub_property: bool = False

    for line_num, line in enumerate(content.splitlines(), start=1):

        # Blank line
        if line.strip() == "":
            continue

        # Continuation line starts with whitespace, and it must be checked
        # before comments, because "  # foo" is a continuation when it
        # follows a property, not a comment. Note that in continuations, # and ;
        # are never treated as comments. They're always part of the value.
        # Inline comment stripping (where "value # comment" strips the comment)
        # only applies to regular property definition lines.
        if line[0] in (" ", "\t"):
            if current_section is None:
                raise ConfigParseError(
                    f"Line {line_num}: Expected a section definition, "
                    f"found continuation"
                )
            if current_key is None:
                raise ConfigParseError(
                    f"Line {line_num}: Expected a property definition, "
                    f"found continuation"
                )

            trimmed = line.strip()

            if in_sub_property:
                _handle_sub_property(
                    trimmed, sections, current_section, current_key, line_num
                )
            else:
                current_value = sections[current_section][current_key]
                sections[current_section][current_key] = current_value + "\n" + trimmed  # type: ignore[operator]
            continue

        # Comment line starts with # or ;
        # No whitespace before # or ;
        if line.startswith(("#", ";")):
            continue

        # Section definition line
        if line.lstrip().startswith("["):
            section_name = _parse_section_line(line, line_num)
            current_section = section_name
            current_key = None
            in_sub_property = False
            if section_name is not None and section_name not in sections:
                sections[section_name] = {}
            continue

        # Property definition line
        if current_section is None:
            raise ConfigParseError(
                f"Line {line_num}: Expected a section definition, found property"
            )

        key, value = _parse_property_line(line, line_num)
        if key is not None:
            current_key = key
            in_sub_property = value == ""
            # We store "" first and later, if an indented 'key = value' line follows,
            # _handle_sub_property promotes it from "" to {}. If no continuation,
            # it stays as ""
            sections[current_section][key] = value

    return sections


def _parse_section_line(line: str, line_num: int) -> str | None:
    """Parse a section definition line like [profile foo]."""
    stripped = line.strip()
    bracket_end = stripped.find("]")
    if bracket_end == -1:
        raise ConfigParseError(f"Line {line_num}: Section definition must end with ']'")
    inner = stripped[1:bracket_end].strip()
    if not inner:
        raise ConfigParseError(f"Line {line_num}: Section name cannot be empty")
    return inner


def _parse_property_line(line: str, line_num: int) -> tuple[str | None, str]:
    """Parse a property definition line like 'key = value'."""
    if "=" not in line:
        raise ConfigParseError(
            f"Line {line_num}: Expected an '=' sign defining a property"
        )

    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip()

    if not key:
        raise ConfigParseError(f"Line {line_num}: Property did not have a name")

    if not _VALID_IDENTIFIER_RE.match(key):
        return None, ""

    key = key.lower()
    value = _strip_inline_comment(value)
    return key, value


def _handle_sub_property(
    line: str,
    sections: RawParsedSections,
    section_name: str,
    parent_key: str,
    line_num: int,
) -> None:
    """Parse a sub-property line (indented key=value under a blank property)."""
    # Promote parent from "" to {} as soon as we enter sub-property handling
    if not isinstance(sections[section_name][parent_key], dict):
        sections[section_name][parent_key] = {}

    if "=" not in line:
        raise ConfigParseError(
            f"Line {line_num}: Expected an '=' sign defining a property in sub-property"
        )

    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip()

    if not key:
        raise ConfigParseError(
            f"Line {line_num}: Property did not have a name in sub-property"
        )

    if not _VALID_IDENTIFIER_RE.match(key):
        return

    key = key.lower()
    # In sub-properties, # and ; are not treated as inline comments.
    # They are included as part of the value

    parent = sections[section_name][parent_key]
    parent[key] = value  # type: ignore[index]


def _strip_inline_comment(value: str) -> str:
    #  '#' and ';' are comments only if preceded by a whitespace
    for i, char in enumerate(value):
        if char in ("#", ";") and i > 0 and value[i - 1] in (" ", "\t"):
            return value[: i - 1].rstrip()
    return value


def _classify_config_section(
    section_name: str,
    properties: dict[str, str | dict[str, str]],
    profiles: ProfileMap,
    sso_sessions: ProfileMap,
    services: ProfileMap,
    has_profile_default: bool,
) -> None:
    stripped = section_name.strip()

    if stripped.startswith("sso-session"):
        name = _extract_prefixed_name(stripped, "sso-session")
        if name and _is_valid_identifier(name):
            _merge_properties(sso_sessions, name, properties)
        return

    if stripped.startswith("services"):
        name = _extract_prefixed_name(stripped, "services")
        if name and _is_valid_identifier(name):
            _merge_properties(services, name, properties)
        return

    if stripped == "default":
        if not has_profile_default:
            _merge_properties(profiles, "default", properties)
        return

    if stripped.startswith("profile"):
        name = _extract_prefixed_name(stripped, "profile")
        if name and _is_valid_identifier(name):
            _merge_properties(profiles, name, properties)
        return


def _classify_credentials_section(
    section_name: str,
    properties: dict[str, str | dict[str, str]],
    profiles: ProfileMap,
) -> None:
    stripped = section_name.strip()

    if stripped.startswith("profile"):
        return
    if stripped.startswith("sso-session"):
        return
    if stripped.startswith("services"):
        return

    if _is_valid_identifier(stripped):
        _merge_properties(profiles, stripped, properties)


def _extract_prefixed_name(section_name: str, prefix: str) -> str | None:
    remainder = section_name[len(prefix) :]
    if not remainder or remainder[0] not in (" ", "\t"):
        return None
    name = remainder.strip()
    return name if name else None


def _is_valid_identifier(name: str) -> bool:
    return bool(_VALID_IDENTIFIER_RE.match(name))


def _is_profile_prefixed_default(section_name: str) -> bool:
    """Check if a section is [profile default]."""
    stripped = section_name.strip()
    if not stripped.startswith("profile"):
        return False
    remainder = stripped[len("profile") :]
    if not remainder or remainder[0] not in (" ", "\t"):
        return False
    return remainder.strip() == "default"


def _merge_properties(
    target: ProfileMap,
    name: str,
    properties: dict[str, str | dict[str, str]],
) -> None:
    """Merge properties into target. Later values win for duplicates."""
    if name not in target:
        target[name] = {}
    target[name].update(properties)
