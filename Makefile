help: ## Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)


install-python-components: ## Builds and installs the python packages.
	./pants package ::
	python3 -m pip install dist/*.whl --force-reinstall


install-java-components: ## Publishes java packages to maven local.
	cd codegen && ./gradlew publishToMavenLocal


install-components: install-python-components install-java-components ## Installs java and python components locally.


smithy-build: ## Builds the Java code generation packages.
	cd codegen && ./gradlew clean build


generate-protocol-tests: ## Generates the protocol tests, rebuilding necessary Java packages.
	cd codegen && ./gradlew clean :smithy-python-protocol-test:build


run-protocol-tests: ## Runs already-generated protocol tests
	cd codegen/smithy-python-protocol-test/build/smithyprojections/smithy-python-protocol-test/rest-json-1/python-client-codegen && \
	python3 -m pip install '.[tests]' && \
	python3 -m pytest tests


test-protocols: install-python-components generate-protocol-tests run-protocol-tests ## Generates and runs protocol tests.
