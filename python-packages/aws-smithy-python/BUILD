resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="README.md")
resource(name="notice", source="NOTICE")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject",
        ":readme",
        ":notice",
        ":requirements",
        "python-packages/aws-smithy-python/aws_smithy_python:source",
        "python-packages/smithy-python:dist",
    ],
    provides=python_artifact(
        name="aws_smithy_python",
        version="0.0.1",
    )
)

python_requirements(
    name="dev-requirements",
    source="requirements-dev.txt",
)

python_requirements(
    name="requirements",
)
