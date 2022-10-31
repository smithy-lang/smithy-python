python_requirements(
    name="requirements-dev.txt",
    source="requirements-dev.txt",
)

python_requirements(
    name="requirements.txt",
)

python_sources(overrides={"setup.py": {"skip_mypy": True}})

python_distribution(
    name="dist",
    provides=python_artifact(
        name="smithy_python",
        version="0.0.1",
    ),
    generate_setup=False,
)
