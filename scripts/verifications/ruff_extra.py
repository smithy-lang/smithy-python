#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Runs ruff rule families not yet enabled in pyproject.toml over shipped code.

These families catch bugs and costs that are cheap to prevent and expensive to
find later: bugbear (B) flags mutable defaults, loop-variable capture and
swallowed exceptions; PERF flags avoidable work in hot loops. Docstring rules
live in the docstrings verification. Kept separate from check-py so the backlog can be measured before the rules are
switched on for good.
"""

import sys
from pathlib import Path

from _common import ROOT, Finding, main, packages, run

_SELECT = "B,PERF"


def check() -> list[Finding]:
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
    findings = [
        Finding(line)
        for line in proc.stdout.splitlines()
        if line.startswith(("/", "packages/"))
    ]
    stats = run(
        [
            ruff,
            "check",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--select",
            _SELECT,
            "--statistics",
            "--no-cache",
            *(str(p.src) for p in packages()),
        ]
    )
    findings.extend(
        Finding(line, severity="info")
        for line in stats.stdout.splitlines()
        if line.strip()
    )
    return findings


if __name__ == "__main__":
    main("extra ruff rules", check)
