# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Generate one AWS SDK client from a sibling aws-sdk-python checkout's model into ./workspace/clients."""

# ruff: noqa: T201, S603, S607

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[1]
WORKSPACE = REPO / "workspace"


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1]:
        sys.exit("usage: make gen <client>   e.g. make gen dynamodb")

    sdk = find_aws_sdk_python()
    model = resolve_model(sdk / "codegen" / "aws-models", sys.argv[1])
    slug = model.stem
    module = "aws_sdk_" + slug.replace("-", "_")
    service = service_id(model)
    version = client_version(sdk / "clients" / f"aws-sdk-{slug}" / "pyproject.toml")

    config = WORKSPACE / ".gen" / slug / "smithy-build.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        json.dumps(
            {
                "version": "1.0",
                "imports": [str(model)],
                "projections": {
                    slug: {
                        "transforms": [
                            {
                                "name": "includeServices",
                                "args": {"services": [service]},
                            },
                            {"name": "removeUnusedShapes"},
                        ],
                        "plugins": {
                            "python-client-codegen": {
                                "service": service,
                                "module": module,
                                "moduleVersion": version,
                            }
                        },
                    }
                },
            },
            indent=4,
        )
        + "\n"
    )
    print(f"generating {module} ({service}) v{version} from {model}")

    subprocess.run(
        [
            str(REPO / "codegen" / "gradlew"),
            "-p",
            str(HARNESS),
            "clean",
            "build",
            "-q",
            f"-PsmithyBuildConfig={config}",
        ],
        check=True,
    )

    projection = (
        HARNESS
        / "build"
        / "smithyprojections"
        / "gen-client"
        / slug
        / "python-client-codegen"
    )
    if not projection.is_dir():
        sys.exit(f"codegen produced no output at {projection}")

    dest = WORKSPACE / "clients" / module
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(projection, dest)

    for cmd in (["ruff", "check", "--fix", "-q"], ["ruff", "format", "-q"]):
        subprocess.run(["uv", "run", *cmd, str(dest)], cwd=REPO, check=True)
    print(f"wrote {dest}")

    # --no-deps keeps this checkout's editable smithy packages instead of resolving published ones.
    subprocess.run(
        ["uv", "pip", "install", "-q", "--no-deps", "-e", str(dest)],
        cwd=REPO,
        check=True,
    )
    print(
        f"installed {module} into {REPO / '.venv'} (run scripts with `uv run python ...`)"
    )


def find_aws_sdk_python() -> Path:
    candidates = []
    if env := os.environ.get("AWS_SDK_PYTHON"):
        candidates.append(Path(env))
    # Checkouts are colocated with a shared prefix, e.g. _4_smithy-python and _4_aws-sdk-python.
    candidates.append(
        REPO.parent / REPO.name.replace("smithy-python", "aws-sdk-python")
    )
    candidates.append(REPO.parent / "aws-sdk-python")
    for candidate in candidates:
        if (candidate / "codegen" / "aws-models").is_dir():
            return candidate.resolve()
    sys.exit(
        "no aws-sdk-python checkout found; tried "
        + ", ".join(str(c) for c in candidates)
        + " (set AWS_SDK_PYTHON to override)"
    )


def resolve_model(models: Path, name: str) -> Path:
    key = name.strip()
    for prefix in ("aws-sdk-", "aws_sdk_"):
        key = key.removeprefix(prefix)
    for candidate in (key, key.replace("_", "-")):
        if (model := models / f"{candidate}.json").exists():
            return model
    available = ", ".join(sorted(p.stem for p in models.glob("*.json")))
    sys.exit(f"no model for '{name}' in {models}\navailable: {available}")


def service_id(model: Path) -> str:
    shapes = json.loads(model.read_text())["shapes"]
    services = [k for k, v in shapes.items() if v.get("type") == "service"]
    if len(services) != 1:
        sys.exit(
            f"expected exactly one service shape in {model.name}, found {services}"
        )
    return services[0]


def client_version(pyproject: Path) -> str:
    if pyproject.exists():
        for line in pyproject.read_text().splitlines():
            if line.startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    return "0.0.1"


if __name__ == "__main__":
    main()
