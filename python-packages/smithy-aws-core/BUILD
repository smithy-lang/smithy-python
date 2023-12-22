resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="README.md")
resource(name="notice", source="NOTICE")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject",
        ":readme",
        ":notice",
        "python-packages/smithy-aws-core/smithy_aws_core:source",
        "python-packages/smithy-core:dist",
    ],
    provides=python_artifact(
        name="smithy_aws_core",
        version="0.0.1",
    ),
)

python_requirements(
    name="dev-requirements",
    source="requirements-dev.txt",
)
