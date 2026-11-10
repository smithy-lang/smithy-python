.DEFAULT_GOAL:=help

.PHONY: help check-imports check-conventions check-api check-dependencies check-packaging check-import-time install format-java check-java build-java generate-protocol-tests generate-codegen-output-py api-snapshot aio-check changelog-check canonical-imports dunder-all source-order dynamic-imports banned-imports ruff-extra docstrings declared-deps import-cycles dep-specifiers package-metadata version-consistency export-names exception-hierarchy secret-repr import-hygiene import-deprecations import-side-effects import-cost wheel-contents type-completeness optional-deps lowest-bounds gen ci lint-py check-py lint-rust check-rust third-party-licenses test-py test-protocols typecheck-protocols static-analysis test-unit test-functional test-integration benchmark build-py clean

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)


# CI runs this target on 3.12 only; see typecheck-protocols.
static-analysis: ## Catches defects CI can find without running the code's tests.
	$(MAKE) check-py
	$(MAKE) aio-check
	$(MAKE) changelog-check
#	$(MAKE) check-imports
#	$(MAKE) check-conventions
#	$(MAKE) check-api
#	$(MAKE) check-dependencies
#	$(MAKE) check-packaging
#	$(MAKE) check-import-time
	$(MAKE) import-cycles # TODO: remove when check-imports passes
	$(MAKE) dynamic-imports # TODO: remove when check-imports passes
	$(MAKE) banned-imports # TODO: remove when check-imports passes
	$(MAKE) api-snapshot # TODO: remove when check-api passes
	$(MAKE) import-deprecations # TODO: remove when check-import-time passes
	$(MAKE) import-cost # TODO: remove when check-import-time passes
	$(MAKE) typecheck-protocols # TODO: remove when check-api passes


test-unit: ## Runs the python unit tests.
	uv run pytest packages/*/tests/unit


# The packages/*/tests/integration suites drive generated clients against
# in-process servers, so they are functional, not live-service, tests.
test-functional: ## Runs the python functional tests and test-protocols.
	$(MAKE) test-protocols
	uv pip install h2 trustme -e "packages/smithy-http[awscrt]"
	uv run pytest packages/*/tests/functional packages/*/tests/integration --no-cov


test-integration: ## Builds and tests the Java codegen and asserts the regenerated snapshots match.
	$(MAKE) build-java
	$(MAKE) generate-protocol-tests
	$(MAKE) generate-codegen-output-py


ci: ## Runs the full CI sequence locally.
	$(MAKE) static-analysis
	$(MAKE) check-rust
	$(MAKE) test-unit
	$(MAKE) test-functional
	$(MAKE) build-py
	$(MAKE) test-integration


########################## Granular targets below ##########################


check-imports: ## Keeps the import graph explicit, acyclic, and free of test-only modules.
	$(MAKE) canonical-imports
	$(MAKE) import-cycles
	$(MAKE) dynamic-imports
	$(MAKE) banned-imports


check-conventions: ## Holds shipped code to our ordering, lint, error, and secret-handling conventions.
	$(MAKE) source-order
	$(MAKE) ruff-extra
	$(MAKE) docstrings
	$(MAKE) exception-hierarchy
	$(MAKE) secret-repr


check-api: ## Keeps the public API surface reviewed, typed, and exported under its own names.
	$(MAKE) api-snapshot
	$(MAKE) export-names
	$(MAKE) dunder-all
	$(MAKE) typecheck-protocols
	$(MAKE) type-completeness


check-dependencies: ## Keeps declared dependencies honest for customers who install only some packages.
	$(MAKE) declared-deps
	$(MAKE) dep-specifiers
	$(MAKE) optional-deps
	$(MAKE) lowest-bounds


check-packaging: ## Keeps what we publish to PyPI consistent across packages.
	$(MAKE) package-metadata
	$(MAKE) version-consistency
	$(MAKE) wheel-contents


check-import-time: ## Keeps importing our packages cheap and free of side effects.
	$(MAKE) import-hygiene
	$(MAKE) import-deprecations
	$(MAKE) import-side-effects
	$(MAKE) import-cost


install: ## Sets up workspace (* you should run this first! *)
	uv sync --all-packages --all-extras
	cd codegen && ./gradlew
	@printf "\n\nWorkspace initialized, please run:\n\033[36msource .venv/bin/activate\033[0m"


format-java: ## Formats the Java code generation packages.
	cd codegen && ./gradlew spotlessApply


check-java: ## Checks Java and Gradle formatting without modifying source.
	cd codegen && ./gradlew spotlessCheck


build-java: ## Builds and tests the Java code generation packages without modifying source.
	cd codegen && ./gradlew clean build


generate-protocol-tests: ## Generates protocol-test clients, copies them to ./codegen-output, and asserts no git diff.
	cd codegen && ./gradlew :protocol-test:clean :protocol-test:build
	rm -rf codegen-output
	mkdir -p codegen-output
	@set -e; for projection_dir in codegen/protocol-test/build/smithyprojections/protocol-test/*/python-client-codegen; do \
		projection=$$(basename $$(dirname "$$projection_dir")); \
		echo "Copying $$projection -> codegen-output/$$projection"; \
		cp -r "$$projection_dir" "codegen-output/$$projection"; \
		echo "Formatting codegen-output/$$projection"; \
		uv run ruff check --fix "codegen-output/$$projection"; \
		uv run ruff format "codegen-output/$$projection"; \
	done
	@if ! git diff --quiet --exit-code -- codegen-output || [ -n "$$(git ls-files --others --exclude-standard -- codegen-output)" ]; then \
		echo "ERROR: generated codegen-output differs from the committed snapshot."; \
		echo "Review the diff and commit it if the change is intended:"; \
		git --no-pager status --short -- codegen-output; \
		git --no-pager diff -- codegen-output; \
		exit 1; \
	fi
	@echo "codegen-output is up to date."


generate-codegen-output-py: ## Generates Python output and asserts no snapshot diff.
	rm -rf codegen-output-py
	uv run python scripts/codegen-output-py/generate.py
	@if ! git diff --quiet --exit-code -- codegen-output-py || [ -n "$$(git ls-files --others --exclude-standard -- codegen-output-py)" ]; then \
		echo "ERROR: generated codegen-output-py differs from the committed snapshot."; \
		echo "Review the diff and commit it if the change is intended:"; \
		git --no-pager status --short -- codegen-output-py; \
		git --no-pager diff -- codegen-output-py; \
		exit 1; \
	fi
	@echo "codegen-output-py is up to date."


api-snapshot: ## Records the public API surface and dual-mode mirrors of each package and asserts no git diff.
	uv run python scripts/api-snapshot/api_snapshot.py


aio-check: ## Enforces aio naming and separation in package sources.
	uv run python scripts/aio-naming/aio_naming.py


changelog-check: ## Asserts the latest commit's package source changes carry changelog fragments of a fitting bump.
	uv run python scripts/changelog/check-fragments.py


canonical-imports: ## Prevents re-export imports, which hide where symbols live and invite cycles.
	uv run python scripts/verifications/canonical_imports.py


dunder-all: ## Keeps __all__ in sync with the public surface that type checkers and docs read.
	uv run python scripts/verifications/dunder_all.py


source-order: ## Keeps the public API at the top of every file and class.
	uv run python scripts/verifications/source_order.py


dynamic-imports: ## Keeps every import visible to static tools.
	uv run python scripts/verifications/dynamic_imports.py


banned-imports: ## Keeps test-only modules out of shipped code.
	uv run python scripts/verifications/banned_imports.py


ruff-extra: ## Measures the backlog for ruff rules not yet enabled.
	uv run python scripts/verifications/ruff_extra.py


docstrings: ## Keeps the public API documented in editors and the API reference.
	uv run python scripts/verifications/docstrings.py


declared-deps: ## Catches imports that only work because of the shared workspace venv.
	uv run python scripts/verifications/declared_deps.py


import-cycles: ## Catches cycles that make import success depend on import order.
	uv run python scripts/verifications/import_cycles.py


dep-specifiers: ## Keeps every part of the repo on the same dependency ranges and in-repo bounds current.
	uv run python scripts/verifications/dep_specifiers.py


package-metadata: ## Catches pyproject.toml drift between packages.
	uv run python scripts/verifications/package_metadata.py


version-consistency: ## Keeps __version__ truthful for user agents and bug reports.
	uv run python scripts/verifications/version_consistency.py


export-names: ## Catches objects exported under a name other than their own.
	uv run python scripts/verifications/export_names.py


exception-hierarchy: ## Lets customers catch every SDK error with one except clause.
	uv run python scripts/verifications/exception_hierarchy.py


secret-repr: ## Keeps credentials out of logs and tracebacks.
	uv run python scripts/verifications/secret_repr.py


import-hygiene: ## Catches modules that only import after a sibling has warmed sys.modules.
	uv run python scripts/verifications/import_hygiene.py


import-deprecations: ## Catches removals that Python or a dependency has already scheduled.
	uv run python scripts/verifications/import_deprecations.py


import-side-effects: ## Keeps imports from overriding the host application's global state.
	uv run python scripts/verifications/import_side_effects.py


import-cost: ## Catches growth in how many of our modules an import loads.
	uv run python scripts/verifications/import_cost.py


wheel-contents: ## Catches wheels that miss source or py.typed, or that ship tests.
	uv run python scripts/verifications/wheel_contents.py


type-completeness: ## Verifies the py.typed promise as a customer's type checker sees it.
	uv run python scripts/verifications/type_completeness.py


optional-deps: ## Checks that a minimal install without extras works or fails clearly.
	uv run python scripts/verifications/optional_deps.py


lowest-bounds: ## Proves the declared lower bounds actually work.
	uv run python scripts/verifications/lowest_bounds.py


# `make gen dynamodb`: the second goal is the client name, so swallow it as a no-op target.
ifeq (gen,$(firstword $(MAKECMDGOALS)))
CLIENT ?= $(word 2,$(MAKECMDGOALS))
ifneq (,$(word 2,$(MAKECMDGOALS)))
$(eval $(word 2,$(MAKECMDGOALS)):;@:)
endif
endif

gen: ## Generates an AWS SDK client from a sibling aws-sdk-python model into ./workspace/clients (make gen dynamodb).
	uv run python scripts/gen-client/gen_client.py "$(CLIENT)"


lint-py: ## Runs linters and formatters on the python packages.
	uv run ruff check packages --fix --config pyproject.toml
	uv run ruff format packages --config pyproject.toml


check-py: ## Runs checks (formatting, lints, type-checking) on the python packages.
	uv run ruff check packages --config pyproject.toml
	uv run ruff format --check --config pyproject.toml
	uv run pyright packages


# Packages with a native extension, each built from a Cargo.toml in the package root.
RUST_MANIFESTS := $(wildcard packages/*/Cargo.toml)

lint-rust: ## Formats and fixes lints in the Rust extensions.
	@set -e; for manifest in $(RUST_MANIFESTS); do \
		cargo fmt --manifest-path "$$manifest"; \
		cargo clippy --manifest-path "$$manifest" --all-targets --fix --allow-dirty --allow-staged; \
	done


check-rust: ## Checks formatting, lints, dependencies, and license attribution of the Rust extensions.
	@set -e; for manifest in $(RUST_MANIFESTS); do \
		dir=$$(dirname "$$manifest"); \
		cargo fmt --manifest-path "$$manifest" --check; \
		cargo clippy --manifest-path "$$manifest" --all-targets --locked -- -D warnings; \
		cargo deny --manifest-path "$$manifest" check; \
		cargo about generate --manifest-path "$$manifest" \
			--output-file "$$dir/LICENSE-THIRD-PARTY.expected" "$$dir/about.hbs"; \
		if ! diff -u "$$dir/LICENSE-THIRD-PARTY" "$$dir/LICENSE-THIRD-PARTY.expected"; then \
			rm "$$dir/LICENSE-THIRD-PARTY.expected"; \
			echo "$$dir/LICENSE-THIRD-PARTY is out of date. Run 'make third-party-licenses'."; \
			exit 1; \
		fi; \
		rm "$$dir/LICENSE-THIRD-PARTY.expected"; \
	done


third-party-licenses: ## Regenerates the third-party license file of each Rust extension from its Cargo.lock.
	@set -e; for manifest in $(RUST_MANIFESTS); do \
		dir=$$(dirname "$$manifest"); \
		cargo about generate --manifest-path "$$manifest" \
			--output-file "$$dir/LICENSE-THIRD-PARTY" "$$dir/about.hbs"; \
	done


test-py: ## Runs tests for the python packages.
	uv run pytest packages


test-protocols: ## Runs the generated protocol-test clients in ./codegen-output; run generate-protocol-tests first after codegen changes.
	uv pip install -e packages/smithy-test
	@set -e; for projection_dir in codegen-output/*/; do \
		uv pip install --no-deps "$$projection_dir"; \
		uv run pytest "$$projection_dir" --no-cov; \
	done


# pyright's wrapper imports typing_extensions, which fails to import on 3.15
# (removed typing.no_type_check_decorator); run the stub type-check on 3.12 only.
typecheck-protocols: ## Type-checks the generated protocol-test stub fixtures in ./codegen-output with pyright.
	@set -e; for projection_dir in codegen-output/*/; do \
		uv pip install --no-deps "$$projection_dir"; \
		uv run pyright "$$projection_dir/tests/_typecheck.py"; \
	done


benchmark: ## Runs ser/deser throughput benchmarks (coverage disabled; not part of CI or the default test run).
	uv run pytest packages/*/tests/benchmark --no-cov -s -q


build-py: ## Builds the python packages.
	uv build --all-packages 


clean: ## Clean up workspace, generated code, and other artifacts.
	uv run virtualenv --clear .venv
	rm -r dist .pytest_cache .ruff_cache || true
	cd codegen && ./gradlew clean
