resource(name="pyproject", source="pyproject.toml")

python_distribution(
    name="dist",
    dependencies=[
        ":pyproject"
    ],
    provides=python_artifact(
        name="smithy_python",
        version="0.0.1",
    )
)
