# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


from typing import Generic, Optional, TypeVar

EntryType = TypeVar("EntryType")


class SmithyEntry(Generic[EntryType]):
    def __init__(self, entry: EntryType, name: str) -> None:
        self.entry: EntryType = entry
        self.name: str = name

    def __repr__(self) -> str:
        return f"SmithyEntry({self.name})"


class SmithyCollection(Generic[EntryType]):
    def __init__(self) -> None:
        self._entries: list[SmithyEntry[EntryType]] = []

    @property
    def entries(self) -> list[SmithyEntry[EntryType]]:
        # TODO: In the future producing this list may be more difficult as
        # entries can be related in more sophisticated ways to allow for
        # merging collections
        return list(self._entries)

    def _resolve_entry_position(self, name: Optional[str], default_pos: int) -> int:
        for n, entry in enumerate(self._entries):
            if entry.name == name:
                return n
        return default_pos

    def add_before(
        self, entry: SmithyEntry[EntryType], name: Optional[str] = None
    ) -> None:
        position = self._resolve_entry_position(name, 0)
        self._entries.insert(position, entry)

    def add_after(
        self, entry: SmithyEntry[EntryType], name: Optional[str] = None
    ) -> None:
        position = self._resolve_entry_position(name, len(self._entries))
        self._entries.insert(position + 1, entry)
