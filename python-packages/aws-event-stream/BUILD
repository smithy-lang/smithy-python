# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="README.md")
resource(name="notice", source="NOTICE")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject",
        ":readme",
        ":notice",
        "python-packages/aws-event-stream/aws_event_stream:source",
    ],
    provides=python_artifact(
        name="aws_event_stream",
        version="0.0.1",
    ),
)

# We shouldn't need this, but pants will assume that smithy_core is an external
# dependency since it's in pyproject.toml and there's no way to exclude it, so
# for now we need to duplicate things.
python_requirements(
    name="requirements",
    source="requirements.txt",
)
