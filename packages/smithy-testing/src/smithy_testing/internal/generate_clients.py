#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Internal script for generating test clients.

This module is used internally by the smithy-testing package to generate
test clients from Smithy models for functional testing. It is not part of
the public API and should not be imported or relied upon externally.
"""

import shutil
import subprocess
from pathlib import Path

# ruff: noqa: T201
# ruff: noqa: S603
# ruff: noqa: S607


def main() -> None:
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent
    clients_dir = package_dir / "clients"

    print("Building clients...")
    added_clients: list[str] = []

    for client_dir in clients_dir.iterdir():
        if not client_dir.is_dir():
            continue

        smithy_build_file = client_dir / "smithy-build.json"
        if not smithy_build_file.exists():
            print(f"  ⚠️ Skipping {client_dir.name} - no smithy-build.json")
            continue

        print(f"  🛠️ Building {client_dir.name}")

        # Run smithy build in client directory
        result = subprocess.run(
            ["smithy", "build"], cwd=client_dir, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Build failed for {client_dir.name}:")
            print(result.stderr)
            continue

        # Copy generated code to codegen directory
        build_dir = client_dir / "build"
        if build_dir.exists():
            # Find generated source directories
            for projection_dir in build_dir.rglob("python-client-codegen/src"):
                for module_dir in projection_dir.iterdir():
                    if module_dir.is_dir():
                        dst_path = client_dir / "codegen" / module_dir.name

                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        if dst_path.exists():
                            shutil.rmtree(dst_path)
                        shutil.copytree(module_dir, dst_path)
                        added_clients.append(module_dir.name)

            # Remove build directory
            shutil.rmtree(build_dir)

    if added_clients:
        print("Generated clients:")
        for client in added_clients:
            print(f"  ✅ {client}")
    else:
        print("⚠️ No clients generated")

    print("Done!")


if __name__ == "__main__":
    main()
