.DEFAULT_GOAL:=help

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)


install: ## Sets up workspace (* you should run this first! *)
	uv sync --all-packages --all-extras
	cd codegen && ./gradlew


build-java: ## Builds the Java code generation packages.
	cd codegen && ./gradlew clean build


test-protocols: ## Generates and runs the restJson1 protocol tests.
	cd codegen && ./gradlew :protocol-test:build
	uv run pytest codegen/protocol-test/build/smithyprojections/protocol-test/rest-json-1/python-client-codegen


lint-py: ## Runs formatters/fixers/linters for the python packages.
	uv run docformatter --wrap-summaries 88 --wrap-description 88 packages -r -i || true
	uv run ruff check packages --fix
	uv run ruff format packages


check-py: ## Runs checkers for the python packages.
	uv run ruff check packages
	uv run pyright packages
	uv run bandit packages -r -x tests


test-py: ## Runs tests for the python packages.
	uv run pytest packages


build-py: lint-py check-py test-py ## Builds (and lints, checks, and tests) the python packages.
	uv build --all-packages 


clean: ## Clean up workspace, generated code, and other artifacts.
	uv run virtualenv --clear .venv
	rm -r dist .pytest_cache .ruff_cache || true
	cd codegen && ./gradlew clean
