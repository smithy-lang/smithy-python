# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

python_test_utils(
    name="test_utils",
    sources=[
        "**/conftest.py",  # pytest's conftest.py file
    ],
)

resource(name="pytyped", source="py.typed")

python_tests(
    name="tests",
    dependencies=[":test_utils", ":pytyped"],
    sources=[
        "**/test_*.py",
        "**/tests.py",
    ],
)
