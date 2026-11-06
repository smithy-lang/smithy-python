#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Fails when the latest commit changes a package's api.json surface without a fitting changelog fragment."""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES_DIR = ROOT / "packages"
API_PATH = "scripts/api-snapshot/api.json"
BASE = "HEAD~1"
FRAGMENT_PATTERN = re.compile(r"^packages/([^/]+)/\.changes/next-release/[^/]+\.json$")
SOURCE_PATTERN = re.compile(r"^packages/([^/]+)/src/")


def main() -> int:
    if (
        _git("rev-parse", "--verify", "--quiet", f"{BASE}^{{commit}}", check=False)
        is None
    ):
        print(
            f"Error: {BASE} is not available; fetch at least two commits of history.",
            file=sys.stderr,
        )
        return 1

    before = _surface(BASE)
    after = _surface("HEAD")
    if before == after:
        print("api.json unchanged in the latest commit.")
        return 0

    changed = (_git("diff", "--name-only", BASE, "HEAD") or "").splitlines()
    sources = {m.group(1) for p in changed if (m := SOURCE_PATTERN.match(p))}
    fragments = _fragment_types(changed)
    errors: list[str] = []
    for package, breaks in sorted(_package_changes(before, after).items()):
        # A surface change with no source change comes from snapshot tooling, not the package.
        if package not in sources:
            continue
        types = fragments.get(package, [])
        if not types:
            errors.append(
                f"{package}: api.json changed but no changelog fragment was added."
            )
            continue
        if not breaks:
            continue
        version = _version(package)
        required = _breaking_bump(version)
        if _bump(types, version) != required:
            listing = "\n".join(f"    {b}" for b in breaks)
            errors.append(
                f"{package} {version}: breaking API change needs a {required} bump, "
                f"but fragments {sorted(set(types))} only impose "
                f"{_bump(types, version)}:\n{listing}"
            )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(
            "\nAdd a fragment with scripts/changelog/new-entry.py in the same commit.",
            file=sys.stderr,
        )
        return 1
    print("Changelog fragments match the api.json changes.")
    return 0


def _package_changes(
    before: dict[str, dict[str, str]], after: dict[str, dict[str, str]]
) -> dict[str, list[str]]:
    """Map each package with a changed surface to its breaking changes.

    :rtype: dict[str, list[str]]
    """
    owners = _module_owners()
    changes: dict[str, list[str]] = {}
    for module in before.keys() | after.keys():
        old = before.get(module)
        new = after.get(module)
        if old == new:
            continue
        package = owners.get(
            module.split(".")[0], module.split(".")[0].replace("_", "-")
        )
        breaks = changes.setdefault(package, [])
        if new is None:
            breaks.append(f"removed module {module}")
            continue
        for name, kind in sorted((old or {}).items()):
            if name not in new:
                breaks.append(f"removed {module}.{name}")
            elif _strip_rex(new[name]) != _strip_rex(kind):
                # Moving a definition behind a re-export keeps it reachable as the same kind.
                breaks.append(f"changed {module}.{name}: {kind} -> {new[name]}")
    return changes


def _bump(types: list[str], version: str) -> str:
    """Mirror the release version planner's bump for a set of fragment types.

    :rtype: str
    """
    if "breaking" in types:
        return _breaking_bump(version)
    if "feature" in types:
        return "minor"
    return "patch"


def _breaking_bump(version: str) -> str:
    """:rtype: str"""
    return "major" if int(version.split(".")[0]) >= 1 else "minor"


def _strip_rex(kind: str) -> str:
    """:rtype: str"""
    return kind.removeprefix("rex-")


def _surface(rev: str) -> dict[str, dict[str, str]]:
    """:rtype: dict[str, dict[str, str]]"""
    text = _git("show", f"{rev}:{API_PATH}", check=False)
    return json.loads(text) if text else {}


def _fragment_types(changed: list[str]) -> dict[str, list[str]]:
    """Collect the types of fragments present at HEAD among the changed paths, by package.

    :rtype: dict[str, list[str]]
    """
    types: dict[str, list[str]] = {}
    for path in changed:
        match = FRAGMENT_PATTERN.match(path)
        if match and (text := _git("show", f"HEAD:{path}", check=False)):
            fragment = json.loads(text)
            types.setdefault(match.group(1), []).append(fragment.get("type", ""))
    return types


def _module_owners() -> dict[str, str]:
    """:rtype: dict[str, str]"""
    return {
        module.name: module.parent.parent.name
        for module in PACKAGES_DIR.glob("*/src/*")
        if (module / "__init__.py").exists()
    }


def _version(package: str) -> str:
    """Read the package version the next release bumps from, as the planner does.

    :rtype: str
    """
    path = PACKAGES_DIR / package
    project = tomllib.loads((path / "pyproject.toml").read_text()).get("project", {})
    if "version" not in project.get("dynamic", []) and project.get("version"):
        return project["version"]
    init = path / "src" / package.replace("-", "_") / "__init__.py"
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', init.read_text(), re.MULTILINE)
    if match is None:
        raise RuntimeError(f"Could not find version for {package} in {init}")
    return match.group(1)


def _git(*args: str, check: bool = True) -> str | None:
    """:rtype: str | None"""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        if check:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return None
    return result.stdout


if __name__ == "__main__":
    sys.exit(main())
