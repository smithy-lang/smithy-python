#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures each ``__all__`` lists the module's public definitions and its re-exports.

Python never checks ``__all__``; only star imports read it. Yet type checkers,
documentation generators and IDEs treat it as the declared public surface, so a
public name missing from it is invisible to them, and a package ``__init__`` that
re-exports a name its source module doesn't export publishes something the owner
never declared public. Unresolvable names are already caught by ruff F822.

Only modules that declare ``__all__`` are checked. A name counts as public when it
is defined in the module and has no leading underscore.
"""

from _common import (
    Finding,
    main,
    module_index,
    owned_roots,
    resolve_from,
    runtime_modules,
)


def check() -> list[Finding]:
    findings: list[Finding] = []
    index = module_index()
    for module in runtime_modules():
        exported = module.dunder_all
        if exported is None:
            continue
        exported_set = set(exported)
        for name in sorted(module.defined):
            if not name.startswith("_") and name not in exported_set:
                findings.append(
                    Finding(f"public {name} is missing from __all__", module.path)
                )
        if not module.is_package:
            continue
        for name, imp in sorted(module.imported.items()):
            if name.startswith("_") or imp.top not in owned_roots() or imp.name is None:
                continue
            target, attr = resolve_from(imp)
            if attr is None:
                continue
            if name not in exported_set:
                findings.append(
                    Finding(
                        f"re-exported {name} (from {target}) is missing from __all__",
                        module.path,
                        imp.line,
                        "warning",
                    )
                )
                continue
            source = index.get(target)
            source_all = source.dunder_all if source is not None else None
            if source_all is not None and attr not in source_all:
                findings.append(
                    Finding(
                        f"re-exports {attr} from {target}, which does not list it in __all__",
                        module.path,
                        imp.line,
                    )
                )
    return findings


if __name__ == "__main__":
    main("__all__ consistency", check)
