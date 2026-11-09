# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Dependency records shared by symbols, writers, and package generation."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Iterator
from dataclasses import dataclass
from typing import Literal

from . import exceptions as _exceptions

__all__ = [
    "HATCHLING",
    "SMITHY_CORE",
    "Dependency",
    "DependencyGroup",
    "DependencySet",
]

type DependencyGroup = Literal["runtime", "build", "test", "docs"]

_GROUP_ORDER: dict[DependencyGroup, int] = {
    "runtime": 0,
    "build": 1,
    "test": 2,
    "docs": 3,
}


@dataclass(frozen=True, slots=True)
class Dependency:
    """A generated package requirement and the group that owns it."""

    package: str
    specifier: str
    group: DependencyGroup
    extras: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.package or self.package.strip() != self.package:
            raise ValueError("Dependency package must be a non-empty trimmed string")
        if self.group not in _GROUP_ORDER:
            raise ValueError(f"Unknown dependency group: {self.group!r}")
        if any(not extra or extra.strip() != extra for extra in self.extras):
            raise ValueError("Dependency extras must be non-empty trimmed strings")
        object.__setattr__(self, "extras", tuple(sorted(set(self.extras))))


class DependencySet(Collection[Dependency]):
    """Deterministic dependencies keyed by package and group."""

    def __init__(self, dependencies: Iterable[Dependency] = ()) -> None:
        self._dependencies: dict[tuple[str, DependencyGroup], Dependency] = {}
        for dependency in dependencies:
            self.add(dependency)

    def add(self, dependency: Dependency) -> None:
        """Add a dependency, merging extras or rejecting version conflicts."""
        key = (dependency.package, dependency.group)
        previous = self._dependencies.get(key)
        if previous is None:
            self._dependencies[key] = dependency
            return
        if previous.specifier != dependency.specifier:
            raise _exceptions.CodegenError(
                f"Conflicting {dependency.group} dependency specifiers for "
                f"{dependency.package!r}: {previous.specifier!r} and "
                f"{dependency.specifier!r}"
            )
        extras = tuple(sorted(set(previous.extras) | set(dependency.extras)))
        if extras != previous.extras:
            self._dependencies[key] = Dependency(
                package=previous.package,
                specifier=previous.specifier,
                group=previous.group,
                extras=extras,
            )

    def for_group(self, group: DependencyGroup) -> tuple[Dependency, ...]:
        """Return one dependency group in deterministic package order."""
        return tuple(dependency for dependency in self if dependency.group == group)

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, Dependency):
            return False
        return self._dependencies.get((value.package, value.group)) == value

    def __iter__(self) -> Iterator[Dependency]:
        return iter(
            sorted(
                self._dependencies.values(),
                key=lambda dependency: (
                    _GROUP_ORDER[dependency.group],
                    dependency.package,
                ),
            )
        )

    def __len__(self) -> int:
        return len(self._dependencies)


SMITHY_CORE = Dependency(
    package="smithy-core",
    specifier="~=0.10.0",
    group="runtime",
)
"""Compatible smithy-core runtime for generated artifacts."""

HATCHLING = Dependency(
    package="hatchling",
    specifier="",
    group="build",
)
"""Build backend used by generated artifacts."""
