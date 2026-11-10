#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures public definitions come before private ones, in modules and in classes.

A reader opening a file should meet its API first and its machinery last. With a
fixed order, the public surface of any file or class is read top-down without
scanning, and review diffs that move a symbol between public and private stand
out. Within a class, dunders (lifecycle) come first, then public members, then
private ones.
"""

import ast
from pathlib import Path

from _common import Finding, main, runtime_modules

type _Def = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def check() -> list[Finding]:
    findings: list[Finding] = []
    for module in runtime_modules():
        top = [n for n in module.tree.body if isinstance(n, _DEF_TYPES)]
        findings.extend(_order(module.path, top, scope="module"))
        for node in ast.walk(module.tree):
            if isinstance(node, ast.ClassDef):
                members = [n for n in node.body if isinstance(n, _DEF_TYPES)]
                findings.extend(
                    _order(module.path, members, scope=f"class {node.name}")
                )
    return findings


_DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _rank(name: str, *, in_class: bool) -> int:
    if in_class and name.startswith("__") and name.endswith("__"):
        return 0
    return 2 if name.startswith("_") else 1


def _order(path: Path, nodes: list[_Def], *, scope: str) -> list[Finding]:
    findings: list[Finding] = []
    in_class = scope != "module"
    highest = 0
    highest_name = ""
    for node in nodes:
        rank = _rank(node.name, in_class=in_class)
        if rank < highest:
            kind = {0: "dunder", 1: "public"}[rank]
            findings.append(
                Finding(
                    f"{scope}: {kind} {node.name} follows {highest_name}",
                    path,
                    node.lineno,
                )
            )
        elif rank > highest:
            highest, highest_name = rank, node.name
    return findings


if __name__ == "__main__":
    main("source order", check)
