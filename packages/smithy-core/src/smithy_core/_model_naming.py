#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Python port of the codegen member-name derivation (PythonSymbolProvider.toMemberName).

CAUTION: this MUST stay bug-for-bug identical to the Java escaper. The generated
conformance test asserts it against the committed generated models for every member.
"""

import re
from collections.abc import Collection

_SNAKE_1 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_SNAKE_2 = re.compile(r"([a-z\d])([A-Z])")
_SNAKE_WS = re.compile(r"(\s|-)")

# reserved-member-names.txt (keywords + used builtins + datetime)
_RESERVED_MEMBERS = frozenset(
    """and as assert async await break class continue def del elif else except
    finally for from global if import in is lambda nonlocal not or pass raise
    return try while with yield bool bytes bytearray dict float int list str
    datetime serialize serialize_members deserialize __init__ __post_init__
    _smithy_default __repr__ __annotations__""".split()
)
# reserved-error-member-names.txt
_RESERVED_ERROR_MEMBERS = frozenset(
    {"is_retry_safe", "retry_after", "is_throttling_error", "fault"}
)
_ERROR_MESSAGE_MEMBER_NAMES = frozenset({"errormessage", "error_message", "message"})
_RESPONSE_METADATA_MEMBER = "response_metadata"


def to_snake_case(word: str) -> str:
    if not word:
        return word
    word = _SNAKE_1.sub(r"\1_\2", word)
    word = _SNAKE_2.sub(r"\1_\2", word)
    word = _SNAKE_WS.sub("_", word)
    return word.lower()


def member_field_name(
    wire_name: str,
    *,
    is_error: bool,
    carries_response_metadata: bool,
    is_enum: bool,
) -> str:
    """Derive the generated python field name for a member.

    :param carries_response_metadata: True if the container is an error or an
        operation output structure (which the generator gives a response_metadata
        attribute).
    """
    if is_error and wire_name.lower() in _ERROR_MESSAGE_MEMBER_NAMES:
        return "message"

    name = to_snake_case(wire_name)
    if name.startswith("__") and not name.endswith("__"):
        name += "___"
    elif name in _RESERVED_MEMBERS:
        name += "_"
    if is_error and name in _RESERVED_ERROR_MEMBERS:
        name += "_"
    if name == _RESPONSE_METADATA_MEMBER and carries_response_metadata:
        name += "_"
    if is_enum:
        name = _escape_enum_underscores(name).upper()
    return name


def _escape_enum_underscores(name: str) -> str:
    if name.startswith("__"):
        return name + "_" if name.endswith("__") and not name.endswith("___") else name
    if name.startswith("_") and name.endswith("_") and not name.endswith("__"):
        return name + "_"
    return name


def variant_class_name(
    container_name: str,
    member_name: str,
    shape_names: Collection[str] = (),
) -> str:
    """Union variant class name: container + capitalized member.

    CAUTION: mirrors PythonSymbolProvider.memberShape -- a synthesized variant name
    that collides with a service-defined shape is disambiguated with a ``_``
    separator (shape names cannot contain ``_``, so this can never re-collide).
    ``shape_names`` must be every shape name in the model for the check to fire.
    """
    capitalized = (
        member_name[:1].upper() + member_name[1:] if member_name else member_name
    )
    name = container_name + capitalized
    if name in shape_names:
        name = container_name + "_" + capitalized
    return name


def union_unknown_name(container_name: str, shape_names: Collection[str] = ()) -> str:
    """Union ``Unknown`` variant name, disambiguated like PythonSymbolProvider.unionShape."""
    name = container_name + "Unknown"
    if name in shape_names:
        name = container_name + "_Unknown"
    return name
