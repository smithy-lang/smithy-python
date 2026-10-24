# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_python.dependencies import (
    HATCHLING,
    SMITHY_CORE,
    Dependency,
    DependencySet,
)
from smithy_python.exceptions import CodegenError


def test_dependency_normalizes_extras() -> None:
    dependency = Dependency(
        package="example",
        specifier="~=1.0",
        group="runtime",
        extras=("xml", "auth", "xml"),
    )
    assert dependency.extras == ("auth", "xml")


@pytest.mark.parametrize(
    "dependency",
    [
        lambda: Dependency("", "", "runtime"),
        lambda: Dependency(" example", "", "runtime"),
        lambda: Dependency("example", "", "invalid"),  # type: ignore[arg-type]
        lambda: Dependency("example", "", "runtime", ("",)),
    ],
)
def test_dependency_rejects_invalid_values(dependency: object) -> None:
    with pytest.raises(ValueError):
        dependency()  # type: ignore[operator]


def test_dependency_set_merges_extras_and_orders_groups() -> None:
    dependencies = DependencySet(
        (
            Dependency("docs", "", "docs"),
            Dependency("testing", "", "test"),
            Dependency("builder", "", "build"),
            Dependency("z-runtime", "~=1.0", "runtime", ("xml",)),
        )
    )
    dependencies.add(Dependency("z-runtime", "~=1.0", "runtime", ("auth", "xml")))
    dependencies.add(Dependency("a-runtime", "~=2.0", "runtime"))

    assert tuple(dependencies) == (
        Dependency("a-runtime", "~=2.0", "runtime"),
        Dependency("z-runtime", "~=1.0", "runtime", ("auth", "xml")),
        Dependency("builder", "", "build"),
        Dependency("testing", "", "test"),
        Dependency("docs", "", "docs"),
    )
    assert dependencies.for_group("runtime") == tuple(dependencies)[:2]


def test_dependency_set_rejects_specifier_conflicts() -> None:
    dependencies = DependencySet((Dependency("example", "~=1.0", "runtime"),))
    with pytest.raises(CodegenError, match="Conflicting runtime dependency"):
        dependencies.add(Dependency("example", "~=2.0", "runtime"))

    assert tuple(dependencies) == (Dependency("example", "~=1.0", "runtime"),)


def test_runtime_dependency_catalog() -> None:
    assert SMITHY_CORE == Dependency("smithy-core", "~=0.10.0", "runtime")
    assert HATCHLING == Dependency("hatchling", "", "build")
