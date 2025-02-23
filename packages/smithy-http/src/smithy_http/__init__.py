# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections import Counter, OrderedDict
from collections.abc import Iterable, Iterator

from . import interfaces
from .interfaces import FieldPosition


class Field(interfaces.Field):
    """A name-value pair representing a single field in an HTTP Request or Response.

    The kind will dictate metadata placement within an HTTP message.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    def __init__(
        self,
        *,
        name: str,
        values: Iterable[str] | None = None,
        kind: FieldPosition = FieldPosition.HEADER,
    ):
        self.name = name
        self.values: list[str] = [val for val in values] if values is not None else []
        self.kind = kind

    def add(self, value: str) -> None:
        """Append a value to a field."""
        self.values.append(value)

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        self.values = values

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        try:
            while True:
                self.values.remove(value)
        except ValueError:
            return

    def as_string(self) -> str:
        """Get comma-delimited string of all values.

        If the ``Field`` has zero values, the empty string is returned. If the ``Field``
        has exactly one value, the value is returned unmodified.

        For ``Field``s with more than one value, the values are joined by a comma and a
        space. For such multi-valued ``Field``s, any values that already contain
        commas or double quotes will be surrounded by double quotes. Within any values
        that get quoted, pre-existing double quotes and backslashes are escaped with a
        backslash.
        """
        value_count = len(self.values)
        if value_count == 0:
            return ""
        if value_count == 1:
            return self.values[0]
        return ", ".join(quote_and_escape_field_value(val) for val in self.values)

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        return [(self.name, val) for val in self.values]

    def __eq__(self, other: object) -> bool:
        """Name, values, and kind must match.

        Values order must match.
        """
        if not isinstance(other, Field):
            return False
        return (
            self.name == other.name
            and self.kind is other.kind
            and self.values == other.values
        )

    def __repr__(self) -> str:
        return f"Field(name={self.name!r}, value={self.values!r}, kind={self.kind!r})"


class Fields(interfaces.Fields):
    def __init__(
        self,
        initial: Iterable[interfaces.Field] | None = None,
        *,
        encoding: str = "utf-8",
    ):
        """Collection of header and trailer entries mapped by name.

        :param initial: Initial list of ``Field`` objects. ``Field``s can also be added
        and later removed.
        :param encoding: The string encoding to be used when converting the ``Field``
        name and value from ``str`` to ``bytes`` for transmission.
        """
        init_fields = [fld for fld in initial] if initial is not None else []
        init_field_names = [self._normalize_field_name(fld.name) for fld in init_fields]
        fname_counter = Counter(init_field_names)
        repeated_names_exist = (
            len(init_fields) > 0 and fname_counter.most_common(1)[0][1] > 1
        )
        if repeated_names_exist:
            non_unique_names = [name for name, num in fname_counter.items() if num > 1]
            raise ValueError(
                "Field names of the initial list of fields must be unique. The "
                "following normalized field names appear more than once: "
                f"{', '.join(non_unique_names)}."
            )
        init_tuples = zip(init_field_names, init_fields)
        self.entries: OrderedDict[str, interfaces.Field] = OrderedDict(init_tuples)
        self.encoding: str = encoding

    def set_field(self, field: interfaces.Field) -> None:
        """Alias for __setitem__ to utilize the field.name for the entry key."""
        self.__setitem__(field.name, field)

    def __setitem__(self, name: str, field: interfaces.Field) -> None:
        """Set or override entry for a Field name."""
        normalized_name = self._normalize_field_name(name)
        normalized_field_name = self._normalize_field_name(field.name)
        if normalized_name != normalized_field_name:
            raise ValueError(
                f"Supplied key {name} does not match Field.name "
                f"provided: {normalized_field_name}"
            )
        self.entries[normalized_name] = field

    def get(
        self, key: str, default: interfaces.Field | None = None
    ) -> interfaces.Field | None:
        return self[key] if key in self else default

    def __getitem__(self, name: str) -> interfaces.Field:
        """Retrieve Field entry."""
        normalized_name = self._normalize_field_name(name)
        return self.entries[normalized_name]

    def __delitem__(self, name: str) -> None:
        """Delete entry from collection."""
        normalized_name = self._normalize_field_name(name)
        del self.entries[normalized_name]

    def get_by_type(self, kind: FieldPosition) -> list[interfaces.Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        return [entry for entry in self.entries.values() if entry.kind is kind]

    def extend(self, other: interfaces.Fields) -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        for other_field in other:
            try:
                cur_field = self.__getitem__(other_field.name)
                for other_value in other_field.values:
                    cur_field.add(other_value)
            except KeyError:
                self.__setitem__(other_field.name, other_field)

    def _normalize_field_name(self, name: str) -> str:
        """Normalize field names.

        For use as key in ``entries``.
        """
        return name.lower()

    def __eq__(self, other: object) -> bool:
        """Encoding must match.

        Entries must match in values and order.
        """
        if not isinstance(other, Fields):
            return False
        return self.encoding == other.encoding and self.entries == other.entries

    def __iter__(self) -> Iterator[interfaces.Field]:
        yield from self.entries.values()

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"Fields({self.entries})"

    def __contains__(self, key: str) -> bool:
        return self._normalize_field_name(key) in self.entries


def quote_and_escape_field_value(value: str) -> str:
    """Escapes and quotes a single :class:`Field` value if necessary.

    See :func:`Field.as_string` for quoting and escaping logic.
    """
    chars_to_quote = (",", '"')
    if any(char in chars_to_quote for char in value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    else:
        return value


def tuples_to_fields(
    tuples: Iterable[tuple[str, str]], *, kind: FieldPosition | None = None
) -> Fields:
    """Convert ``name``, ``value`` tuples to ``Fields`` object. Each tuple represents
    one Field value.

    :param kind: The Field kind to define for all tuples.
    """
    fields = Fields()
    for name, value in tuples:
        try:
            fields[name].add(value)
        except KeyError:
            fields[name] = Field(
                name=name, values=[value], kind=kind or FieldPosition.HEADER
            )

    return fields
