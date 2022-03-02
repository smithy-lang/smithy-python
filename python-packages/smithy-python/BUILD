python_requirements(
    source="requirements-dev.txt",
)

python_requirements()

python_sources(
    overrides={
        "setup.py": {"skip_mypy": True}
    }
)

python_distribution(
    name="dist",
    provides=python_artifact(
        name="smithy_python",
        version="0.0.1",
    )
)
