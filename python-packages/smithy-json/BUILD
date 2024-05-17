resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="README.md")
resource(name="notice", source="NOTICE")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject",
        ":readme",
        ":notice",
        "python-packages/smithy-json/smithy_json:source",
        "python-packages/smithy-core:dist",
    ],
    provides=python_artifact(
        name="smithy_json",
        version="0.0.1",
    ),
)
