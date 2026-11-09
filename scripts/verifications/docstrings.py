#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures public classes, functions, methods and constants have docstrings.

Docstrings are the API reference customers read in their editor and in the
generated docs; an undocumented public symbol is a blank page there. Internal
symbols (underscore-prefixed, dunders, or anything in an underscore-prefixed
module) are exempt, since nobody outside the package reads them. Classes,
functions and methods are checked with ruff's pydocstyle rules. Module-level
constants carry an attribute docstring (a string literal right after the
assignment), which no ruff rule checks, so that part is an AST pass.
"""

import ast
import re
import sys
from pathlib import Path

from _common import ROOT, Finding, main, packages, run, runtime_modules

_SELECT = "D101,D102,D103,D106"
_CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]*$")


def check() -> list[Finding]:
    return [*_ruff_findings(), *_constant_findings()]


def _ruff_findings() -> list[Finding]:
    ruff = str(Path(sys.executable).parent / "ruff")
    proc = run(
        [
            ruff,
            "check",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--select",
            _SELECT,
            "--output-format",
            "concise",
            "--no-cache",
            *(str(p.src) for p in packages()),
        ]
    )
    return [
        Finding(line)
        for line in proc.stdout.splitlines()
        if line.startswith(("/", "packages/"))
    ]


def _constant_findings() -> list[Finding]:
    findings: list[Finding] = []
    for module in runtime_modules():
        if not module.public:
            continue
        body = module.tree.body
        for index, node in enumerate(body):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            elif isinstance(node, ast.AnnAssign):
                target = node.target
            else:
                continue
            if not isinstance(target, ast.Name) or not _CONSTANT.match(target.id):
                continue
            following = body[index + 1] if index + 1 < len(body) else None
            documented = (
                isinstance(following, ast.Expr)
                and isinstance(following.value, ast.Constant)
                and isinstance(following.value.value, str)
            )
            if not documented:
                findings.append(
                    Finding(
                        f"public constant {target.id} has no docstring",
                        module.path,
                        node.lineno,
                    )
                )
    return findings


if __name__ == "__main__":
    main("docstrings", check)
