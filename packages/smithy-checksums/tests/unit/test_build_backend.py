# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import importlib.util
import shutil
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

_BACKEND_PATH = (
    Path(__file__).parents[2] / "build_backend" / "smithy_checksums_build.py"
)
_ENV_VAR = "SMITHY_PYTHON_NATIVE_BUILD"


@pytest.fixture
def backend() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "smithy_checksums_build", _BACKEND_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _set_toolchain(
    monkeypatch: pytest.MonkeyPatch,
    backend: ModuleType,
    *,
    installed: bool = True,
    version: tuple[int, ...] | None = (1, 93, 0),
) -> None:
    tools = {"cargo": "/bin/cargo", "rustc": "/bin/rustc"} if installed else {}
    monkeypatch.setattr(shutil, "which", tools.get)
    monkeypatch.setattr(backend, "_rustc_version", lambda _: version)  # type: ignore


def _set_mode(monkeypatch: pytest.MonkeyPatch, mode: str | None) -> None:
    if mode is None:
        monkeypatch.delenv(_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(_ENV_VAR, mode)


def _requires_native(backend: ModuleType) -> bool:
    requires = backend.get_requires_for_build_wheel()
    native = any(req.startswith("maturin") for req in requires)
    assert ("hatchling" in requires) is not native

    editable_requires = backend.get_requires_for_build_editable()
    assert ("editables" in editable_requires) is not native
    return native


@pytest.mark.parametrize(
    ("mode", "installed", "native"),
    [
        (None, True, True),
        (None, False, False),
        ("auto", True, True),
        ("AUTO", False, False),
        ("always", True, True),
        ("never", True, False),
        ("never", False, False),
    ],
)
def test_selects_backend(
    backend: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    mode: str | None,
    installed: bool,
    native: bool,
) -> None:
    _set_mode(monkeypatch, mode)
    _set_toolchain(monkeypatch, backend, installed=installed)
    assert _requires_native(backend) is native


@pytest.mark.parametrize("mode", [None, "never", "always"])
def test_sdist_never_needs_rust(
    backend: ModuleType, monkeypatch: pytest.MonkeyPatch, mode: str | None
) -> None:
    _set_mode(monkeypatch, mode)
    _set_toolchain(monkeypatch, backend, installed=False)
    assert backend.get_requires_for_build_sdist() == ["hatchling"]


@pytest.mark.parametrize("mode", [None, "always"])
def test_rejects_old_rust(
    backend: ModuleType, monkeypatch: pytest.MonkeyPatch, mode: str | None
) -> None:
    _set_mode(monkeypatch, mode)
    _set_toolchain(monkeypatch, backend, version=(1, 70, 0))
    with pytest.raises(RuntimeError, match=r"requires Rust 1\.89.*found 1\.70\.0") as e:
        backend.get_requires_for_build_wheel()
    assert f"{_ENV_VAR}=never" in str(e.value)


def test_always_requires_rust(
    backend: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_mode(monkeypatch, "always")
    _set_toolchain(monkeypatch, backend, installed=False)
    with pytest.raises(RuntimeError, match="no Rust toolchain was found") as e:
        backend.get_requires_for_build_wheel()
    assert f"{_ENV_VAR}=never" in str(e.value)


def test_unknown_rust_version_builds_natively(
    backend: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_mode(monkeypatch, None)
    _set_toolchain(monkeypatch, backend, version=None)
    assert _requires_native(backend)


def test_failed_native_build_suggests_pure_python(
    backend: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(wheel_directory: str, config_settings: object) -> str:
        raise SystemExit(1)

    _set_mode(monkeypatch, None)
    _set_toolchain(monkeypatch, backend)
    monkeypatch.setattr(
        backend,
        "import_module",
        lambda _: SimpleNamespace(build_wheel=fail),  # type: ignore
    )
    with pytest.raises(SystemExit):
        backend.build_wheel("dist")
    assert f"{_ENV_VAR}=never" in capsys.readouterr().err


def test_rejects_unknown_mode(
    backend: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_mode(monkeypatch, "sometimes")
    with pytest.raises(ValueError, match="sometimes"):
        backend.get_requires_for_build_wheel()


def test_minimum_rust_version_matches_cargo_toml(backend: ModuleType) -> None:
    assert backend._minimum_rust_version() == (1, 89)


@pytest.mark.parametrize(
    ("output", "version"),
    [
        ("rustc 1.93.0 (254b59607 2026-01-19)\n", (1, 93, 0)),
        ("rustc 1.95.0-nightly (0123abcde 2026-02-01)\n", (1, 95, 0)),
        ("error: no default toolchain configured\n", None),
        ("", None),
    ],
)
def test_parses_rustc_version(
    backend: ModuleType, output: str, version: tuple[int, ...] | None
) -> None:
    assert backend._parse_rustc_version(output) == version
