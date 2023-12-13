resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="README.md")
resource(name="notice", source="NOTICE")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject",
        ":readme",
        ":notice",
        "python-packages/smithy-http/smithy_http:source",
    ],
    provides=python_artifact(
        name="smithy_http",
        version="0.0.1",
    ),
)

python_requirements(source="pyproject.toml")
