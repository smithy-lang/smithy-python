.DEFAULT_GOAL:=help

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)


install: ## Sets up workspace (* you should run this first! *)
	uv sync --all-packages --all-extras
	cd codegen && ./gradlew
	@printf "\n\nWorkspace initialized, please run:\n\033[36msource .venv/bin/activate\033[0m"


build-java: ## Builds the Java code generation packages.
	cd codegen && ./gradlew clean build


test-protocols: ## Generates and runs protocol tests for all supported protocols.
	cd codegen && ./gradlew :protocol-test:clean :protocol-test:build
	@set -e; for projection_dir in codegen/protocol-test/build/smithyprojections/protocol-test/*/python-client-codegen; do \
		uv pip install "$$projection_dir"; \
		uv run pytest "$$projection_dir"; \
	done


lint-py: ## Runs linters and formatters on the python packages.
	uv run ruff check packages --fix --config pyproject.toml
	uv run ruff format packages --config pyproject.toml


check-py: ## Runs checks (formatting, lints, type-checking) on the python packages.
	uv run ruff check packages --config pyproject.toml
	uv run ruff format --check --config pyproject.toml
	uv run pyright packages


test-py: ## Runs tests for the python packages.
	uv run pytest packages


build-py: ## Builds the python packages.
	uv build --all-packages 


clean: ## Clean up workspace, generated code, and other artifacts.
	uv run virtualenv --clear .venv
	rm -r dist .pytest_cache .ruff_cache || true
	cd codegen && ./gradlew clean
