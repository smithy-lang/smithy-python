# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

resource(name="pytyped", source="py.typed")

python_sources(
    name="source",
    dependencies=[
        ":pytyped",
        "python-packages/smithy-http:requirements",
    ],
    sources=["**/*.py"],
)
