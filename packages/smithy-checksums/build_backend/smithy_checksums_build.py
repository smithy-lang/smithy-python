#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""PEP 517 build backend for smithy-checksums.

Wheels are built with maturin, including the native extension, when a Rust
toolchain is available. Without one, they're built with hatchling and contain only
the pure-Python implementation, which the package also falls back to at runtime.
If a Rust toolchain is available but can't build the extension, for example because
it's too old, the build fails with instructions rather than silently falling back.

Source distributions are always built with hatchling, since maturin needs cargo to
build them. The contents are the same either way.

Set ``SMITHY_PYTHON_NATIVE_BUILD`` to control which backend builds wheels:

* ``auto`` (the default): maturin if ``cargo`` is on the ``PATH``, else hatchling.
* ``always``: maturin, failing if the extension can't be built.
* ``never``: hatchling, producing a ``py3-none-any`` wheel.
"""

import os
import re
import shutil
import subprocess
import sys
import tomllib
from importlib import import_module
from pathlib import Path

type _ConfigSettings = dict[str, str | list[str]] | None
type _Version = tuple[int, ...]

_ENV_VAR = "SMITHY_PYTHON_NATIVE_BUILD"
_MATURIN = "maturin>=1.10,<2"
_HATCHLING = "hatchling"
_CARGO_TOML = Path(__file__).parent.parent / "Cargo.toml"
_PURE_PYTHON_HINT = (
    f"To install the pure-Python implementation instead, set {_ENV_VAR}=never. It "
    "produces identical checksums, but CRC32C and CRC64NVME are much slower."
)


def _build_native() -> bool:
    mode = os.environ.get(_ENV_VAR, "auto").strip().lower()
    match mode:
        case "auto":
            if shutil.which("cargo") is None:
                return False
        case "always":
            pass
        case "never":
            return False
        case _:
            raise ValueError(
                f"{_ENV_VAR} must be 'auto', 'always', or 'never', not {mode!r}"
            )
    _check_rust_toolchain()
    return True


def _check_rust_toolchain() -> None:
    """Fails early, with instructions, if the Rust toolchain can't build the extension."""
    minimum = _minimum_rust_version()
    required = ".".join(map(str, minimum))
    rustc = shutil.which("rustc")
    if shutil.which("cargo") is None or rustc is None:
        raise RuntimeError(
            f"Building the smithy-checksums native extension requires Rust {required} "
            f"or newer, but no Rust toolchain was found. Install one from "
            f"https://rustup.rs. {_PURE_PYTHON_HINT}"
        )
    found = _rustc_version(rustc)
    # If the version can't be determined, let the build itself decide.
    if found is not None and found < minimum:
        raise RuntimeError(
            f"Building the smithy-checksums native extension requires Rust {required} "
            f"or newer, but found {'.'.join(map(str, found))}. Upgrade Rust, for "
            f"example with `rustup update`. {_PURE_PYTHON_HINT}"
        )


def _minimum_rust_version() -> _Version:
    with _CARGO_TOML.open("rb") as manifest:
        rust_version: str = tomllib.load(manifest)["package"]["rust-version"]
    return tuple(int(part) for part in rust_version.split("."))


def _rustc_version(rustc: str) -> _Version | None:
    try:
        result = subprocess.run(  # noqa: S603
            [rustc, "--version"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return _parse_rustc_version(result.stdout)


def _parse_rustc_version(output: str) -> _Version | None:
    match = re.match(r"rustc (\d+)\.(\d+)\.(\d+)", output)
    return None if match is None else tuple(int(part) for part in match.groups())


def _build(hook: str, wheel_directory: str, config_settings: _ConfigSettings) -> str:
    if not _build_native():
        backend = import_module("hatchling.build")
        return getattr(backend, hook)(wheel_directory, config_settings)
    try:
        return getattr(import_module("maturin"), hook)(wheel_directory, config_settings)
    except (Exception, SystemExit):
        # maturin prints the compiler output and exits the process on failure.
        sys.stderr.write(
            "\nBuilding the smithy-checksums native extension failed. "
            f"{_PURE_PYTHON_HINT}\n"
        )
        raise


def get_requires_for_build_wheel(config_settings: _ConfigSettings = None) -> list[str]:
    return [_MATURIN] if _build_native() else [_HATCHLING]


def get_requires_for_build_editable(
    config_settings: _ConfigSettings = None,
) -> list[str]:
    return [_MATURIN] if _build_native() else [_HATCHLING, "editables"]


def get_requires_for_build_sdist(config_settings: _ConfigSettings = None) -> list[str]:
    return [_HATCHLING]


def build_wheel(
    wheel_directory: str,
    config_settings: _ConfigSettings = None,
    metadata_directory: str | None = None,
) -> str:
    return _build("build_wheel", wheel_directory, config_settings)


def build_editable(
    wheel_directory: str,
    config_settings: _ConfigSettings = None,
    metadata_directory: str | None = None,
) -> str:
    return _build("build_editable", wheel_directory, config_settings)


def build_sdist(sdist_directory: str, config_settings: _ConfigSettings = None) -> str:
    return import_module("hatchling.build").build_sdist(
        sdist_directory, config_settings
    )
