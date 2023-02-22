# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

python_test_utils(
    name="test_utils",
    sources=[
        "**/conftest.py",  # pytest's conftest.py file
        "**/*_utils.py",  # all other utils files must be named to match this pattern
    ]
)

resource(name="pytyped", source="py.typed")

python_tests(
    name="tests",
    dependencies=[":test_utils", ":pytyped"],
    sources=[
        "unit/**/test_*.py",
        "unit/**/tests.py",
        "functional/**/test_*.py",
        "functional/**/tests.py",
        "integration/**/test_*.py",
        "integration/**/tests.py",
    ]
)
