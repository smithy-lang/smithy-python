#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ensures every symbol in each package's public API is fully typed.

Shipping ``py.typed`` promises customers that our public API is typed. Pyright's
strict mode on our own sources doesn't verify that promise: inferred return
types, unannotated public attributes and partially unknown types type-check
internally but show up as ``Unknown`` in a customer's editor and type checker.
``pyright --verifytypes`` measures the public surface the way a consumer sees it.

It only resolves installed (non-editable) packages, so the wheels are built and
installed into a temporary venv first.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

from _common import Finding, build_wheels, main, make_venv, packages, run

_SHOWN_PER_PACKAGE = 20


def check() -> list[Finding]:
    findings: list[Finding] = []
    pyright = str(Path(sys.executable).parent / "pyright")
    with tempfile.TemporaryDirectory(prefix="type-completeness-") as tmp:
        work = Path(tmp)
        wheels = build_wheels(work / "wheels")
        venv = work / "venv"
        make_venv(venv, *map(str, wheels))
        for package in packages():
            for root in package.roots:
                proc = run(
                    [
                        pyright,
                        "--verifytypes",
                        root,
                        "--ignoreexternal",
                        "--outputjson",
                    ],
                    cwd=work,
                    env={
                        "VIRTUAL_ENV": str(venv),
                        "PATH": f"{venv / 'bin'}:{os.environ['PATH']}",
                    },
                )
                findings.extend(
                    _report(package.src / root, root, proc.stdout, proc.stderr)
                )
    return findings


def _report(path: Path, root: str, stdout: str, stderr: str) -> list[Finding]:
    try:
        completeness = json.loads(stdout)["typeCompleteness"]
    except (json.JSONDecodeError, KeyError):
        return [Finding(f"{root}: pyright failed: {stderr.strip()[-300:]}", path)]
    if not completeness.get("packageRootDirectory"):
        return [Finding(f"{root}: pyright did not resolve the installed package", path)]
    score = completeness["completenessScore"]
    if score >= 1:
        return []
    counts = completeness["exportedSymbolCounts"]
    total = sum(counts.values())
    findings = [
        Finding(f"{root}: {score:.1%} of {total} exported symbols fully typed", path)
    ]
    incomplete = [
        s for s in completeness["symbols"] if s["isExported"] and not s["isTypeKnown"]
    ]
    for symbol in incomplete[:_SHOWN_PER_PACKAGE]:
        first = next(
            (
                d["message"].splitlines()[0]
                for d in symbol["diagnostics"]
                if d["severity"] == "error"
            ),
            "type not known",
        )
        findings.append(Finding(f"  {symbol['name']}: {first}", path, severity="info"))
    if len(incomplete) > _SHOWN_PER_PACKAGE:
        findings.append(
            Finding(
                f"  ... {len(incomplete) - _SHOWN_PER_PACKAGE} more",
                path,
                severity="info",
            )
        )
    return findings


if __name__ == "__main__":
    main("type completeness", check)
