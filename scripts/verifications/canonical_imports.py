#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures our own code imports each of our symbols from the module that defines it.

Importing through a re-export makes the importer depend on the re-exporting
module's import order and contents, which is how import cycles and accidental
public-surface dependencies creep in. It also hides where a symbol lives from
readers and refactoring tools. A re-export import is accepted under a private
local name (``import X as _X``), which marks it as a deliberate, module-internal
choice, and when the defining module is private, since the re-export is then the
symbol's public home.

Covers package sources and the generated test clients.
"""

from _common import (
    Finding,
    canonical_definition,
    generated_modules,
    main,
    module_index,
    owned_roots,
    resolve_from,
    runtime_modules,
)


def check() -> list[Finding]:
    findings: list[Finding] = []
    index = module_index()
    roots = owned_roots() | {m.name.split(".")[0] for m in generated_modules()}
    for module in [*runtime_modules(), *generated_modules()]:
        for imp in module.imports:
            if imp.name is None or imp.name == "*" or imp.top not in roots:
                continue
            target, attr = resolve_from(imp)
            if attr is None:
                continue
            source = index.get(target)
            if source is None:
                findings.append(
                    Finding(
                        f"cannot resolve module {target}",
                        module.path,
                        imp.line,
                        "warning",
                    )
                )
                continue
            if attr in source.defined:
                continue
            if imp.asname is not None and imp.asname.startswith("_"):
                continue
            canonical = canonical_definition(target, attr)
            if canonical is None:
                findings.append(
                    Finding(
                        f"{attr} is not defined or imported in {target}",
                        module.path,
                        imp.line,
                        "warning",
                    )
                )
                continue
            if any(part.startswith("_") for part in canonical.split(".")):
                continue
            findings.append(
                Finding(
                    f"imports {attr} from re-exporting {target}; defined in {canonical}",
                    module.path,
                    imp.line,
                )
            )
    return findings


if __name__ == "__main__":
    main("canonical imports", check)
