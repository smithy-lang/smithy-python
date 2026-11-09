#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Bans ``importlib.import_module`` and ``__import__`` with non-literal arguments in shipped code.

An import whose target is computed at runtime is invisible to every static tool:
the dependency, cycle, import-direction and canonical-import verifications,
type checkers, bundlers and freezers all miss it. Requiring a string literal
keeps the import graph those tools see complete.
"""

import ast

from _common import Finding, main, runtime_modules


def check() -> list[Finding]:
    findings: list[Finding] = []
    for module in runtime_modules():
        aliases = _import_module_aliases(module.tree)
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Call) or not _is_dynamic_import(
                node.func, aliases
            ):
                continue
            first = node.args[0] if node.args else None
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                findings.append(
                    Finding(
                        f"dynamic import with non-literal target: {ast.unparse(node)[:120]}",
                        module.path,
                        node.lineno,
                    )
                )
    return findings


def _import_module_aliases(tree: ast.Module) -> set[str]:
    names = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name in ("import_module", "__import__"):
                    names.add(alias.asname or alias.name)
    return names


def _is_dynamic_import(func: ast.expr, aliases: set[str]) -> bool:
    if isinstance(func, ast.Name):
        return func.id in aliases
    return (
        isinstance(func, ast.Attribute)
        and func.attr in ("import_module", "__import__")
        and isinstance(func.value, ast.Name)
        and func.value.id == "importlib"
    )


if __name__ == "__main__":
    main("dynamic imports", check)
