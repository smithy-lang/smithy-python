resource(name="pytyped", source="py.typed")

python_sources(
    name="source",
    dependencies=[":pytyped"],
    sources=["**/*.py"],
    overrides={
        "_private/rfc3986/*.py": {"skip_mypy": True}
    }
)
