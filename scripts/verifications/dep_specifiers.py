#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures dependency specifiers agree across packages and track in-repo versions.

uv.lock resolves one version for the whole workspace, so diverging specifiers for
the same third-party dependency go unnoticed here, but a customer installing a
subset of our packages gets whatever range happens to apply, and two packages may
be uninstallable together. In-repo dependencies must be bounded and satisfied by
the sibling's current version, or a release can float onto a sibling version
that lacks the code it needs.
"""

from _common import Finding, main, package_by_dist, packages
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name


def check() -> list[Finding]:
    findings: list[Finding] = []
    siblings = package_by_dist()
    specs: dict[str, dict[str, list[str]]] = {}
    for package in packages():
        reqs = [("dependencies", r) for r in package.dependencies] + [
            (f"extra {extra}", r) for extra, rs in package.extras.items() for r in rs
        ]
        for where, req in reqs:
            name = canonicalize_name(req.name)
            sibling = siblings.get(name)
            if sibling is None:
                specs.setdefault(name, {}).setdefault(
                    str(req.specifier) or "(any)", []
                ).append(f"{package.dist} {where}")
                continue
            version = sibling.current_version
            pyproject = package.dir / "pyproject.toml"
            if not req.specifier:
                findings.append(
                    Finding(
                        f"{package.dist} {where}: in-repo {name} is unbounded",
                        pyproject,
                    )
                )
            elif version is not None and not SpecifierSet(str(req.specifier)).contains(
                version, prereleases=True
            ):
                findings.append(
                    Finding(
                        f"{package.dist} {where}: in-repo {name}{req.specifier} excludes "
                        f"its current version {version}",
                        pyproject,
                    )
                )
    for name, variants in sorted(specs.items()):
        if len(variants) > 1:
            listed = "; ".join(
                f"{s} ({', '.join(users)})" for s, users in sorted(variants.items())
            )
            findings.append(Finding(f"{name} has {len(variants)} specifiers: {listed}"))
    return findings


if __name__ == "__main__":
    main("dependency specifiers", check)
