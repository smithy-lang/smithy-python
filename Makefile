.DEFAULT_GOAL:=help

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

pants: ## Installs pants launcher binary using the get-pants script. If $CI is true, assume it's installed already (through GHA), so just copy the wrapper script.
ifeq ($(CI),true)
	cp scripts/pantsw pants
else
	./get-pants --bin-dir .
endif


install-python-components: pants ## Packages and installs the python packages.
	./pants package ::
	python3 -m pip install dist/*.whl --force-reinstall


install-java-components: ## Publishes java packages to maven local.
	cd codegen && ./gradlew publishToMavenLocal


install-components: install-python-components install-java-components ## Installs java and python components locally.


smithy-build: ## Builds the Java code generation packages.
	cd codegen && ./gradlew clean build


generate-protocol-tests: ## Generates the protocol tests, rebuilding necessary Java packages.
	cd codegen && ./gradlew :protocol-test:build


run-protocol-tests: ## Runs already-generated protocol tests.
	cd codegen/protocol-test/build/smithyprojections/protocol-test/rest-json-1/python-client-codegen && \
	python3 -m pip install '.[tests]' && \
	python3 -m pytest tests


test-protocols: install-python-components generate-protocol-tests run-protocol-tests ## Generates and runs protocol tests.


lint-py: pants ## Runs formatters/fixers/linters for the python packages.
	./pants fix lint python-packages/smithy-core::
	./pants fix lint python-packages/smithy-http::
	./pants fix lint python-packages/smithy-aws-core::
	./pants fix lint python-packages/smithy-json::
	./pants fix lint python-packages/smithy-event-stream::
	./pants fix lint python-packages/aws-event-stream::


check-py: pants ## Runs checkers for the python packages.
	./pants check python-packages/smithy-core::
	./pants check python-packages/smithy-http::
	./pants check python-packages/smithy-aws-core::
	./pants check python-packages/smithy-json::
	./pants check python-packages/smithy-event-stream::
	./pants check python-packages/aws-event-stream::


test-py: pants ## Runs tests for the python packages.
	./pants test python-packages/smithy-core::
	./pants test python-packages/smithy-http::
	./pants test python-packages/smithy-aws-core::
	./pants test python-packages/smithy-json::
	./pants test python-packages/smithy-event-stream::
	./pants test python-packages/aws-event-stream::


build-py: lint-py check-py test-py ## Runs formatters/fixers/linters/checkers/tests for the python packages.


clean: ## Clean up generated code and artifacts.
	rm -rf dist/
	cd codegen && ./gradlew clean
