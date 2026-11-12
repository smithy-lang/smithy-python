#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures each package's ``__version__`` matches its distribution version.

``__version__`` is what user-agent strings, bug reports and customer feature
gates read; the distribution version is what resolvers and PyPI read. If they
disagree, telemetry and support misattribute behavior to the wrong release. The
version should also come from one place, sourced the same way in every package.

Everything is read from the source tree, because installed metadata lags the
source whenever an editable install isn't rebuilt after a version bump.
"""

import ast
from pathlib import Path

from _common import Finding, Package, main, packages


def check() -> list[Finding]:
    findings: list[Finding] = []
    for package in packages():
        pyproject = package.dir / "pyproject.toml"
        project = package.pyproject["project"]
        dynamic = "version" in project.get("dynamic", [])
        if package.maturin:
            findings.extend(_check_static(package, str(project.get("version"))))
        elif not dynamic:
            findings.append(
                Finding(
                    f"{package.dist}: static version {project.get('version')!r} in pyproject.toml; "
                    "other packages read it from __version__",
                    pyproject,
                )
            )
        else:
            findings.extend(_check_dynamic(package))
    return findings


def _check_dynamic(package: Package) -> list[Finding]:
    """Hatch reads the version file, so every root must agree with its literal."""
    pyproject = package.dir / "pyproject.toml"
    version_file = package.version_file
    if version_file is None:
        return [
            Finding(
                f"{package.dist}: dynamic version without a hatch version path",
                pyproject,
            )
        ]
    if not version_file.exists():
        return [
            Finding(f"{package.dist}: hatch version path does not exist", pyproject)
        ]
    expected = _literal_version(version_file)
    if expected is None:
        return [
            Finding(
                f"{package.dist}: hatch version path has no literal __version__",
                version_file,
            )
        ]
    findings: list[Finding] = []
    for root in package.roots:
        init = package.src / root / "__init__.py"
        found = _literal_version(init)
        if found is None:
            findings.append(Finding(f"{root} defines no literal __version__", init))
        elif found != expected:
            findings.append(
                Finding(
                    f"{root}.__version__ is {found!r}, distribution version is {expected!r}",
                    init,
                )
            )
    return findings


def _check_static(package: Package, expected: str) -> list[Finding]:
    """maturin reads only a static version, so __version__ may defer to its metadata."""
    findings: list[Finding] = []
    for root in package.roots:
        init = package.src / root / "__init__.py"
        value = _version_value(init)
        if value is None:
            findings.append(Finding(f"{root} defines no __version__", init))
        elif _reads_own_metadata(value, package.dist):
            continue
        elif not (isinstance(value, ast.Constant) and value.value == expected):
            findings.append(
                Finding(
                    f"{root}.__version__ does not match the static version {expected!r}",
                    init,
                )
            )
    return findings


def _version_value(path: Path) -> ast.expr | None:
    if not path.exists():
        return None
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets
        ):
            return node.value
    return None


def _literal_version(path: Path) -> str | None:
    value = _version_value(path)
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _reads_own_metadata(value: ast.expr, dist: str) -> bool:
    """Whether value is ``version("<dist>")``, the distribution's own metadata."""
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name | ast.Attribute)
        and (value.func.id if isinstance(value.func, ast.Name) else value.func.attr)
        == "version"
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Constant)
        and value.args[0].value == dist
    )


if __name__ == "__main__":
    main("version consistency", check)
