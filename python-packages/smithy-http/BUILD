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
        "python-packages/smithy-core:dist",
    ],
    provides=python_artifact(
        name="smithy_http",
        version="0.0.1",
    ),
)

# We shouldn't need this, but pants will assume that smithy-core is an external
# dependency since it's in pyproject.toml and there's no way to exclude it, so
# for now we need to duplicate things.
python_requirements(
    name="requirements",
    source="requirements.txt",
)

# python_requirements(
#     name="pyproject-requirements",
#     source="pyproject.toml",
# )
