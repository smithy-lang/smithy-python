help: ## Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)


## Installs pants launcher binary using the get-pants script.
## If $CI is true, assume it's installed already (through GHA), so just copy the wrapper script.
pants:
ifeq ($(CI),true)
	cp scripts/pantsw pants
else
	./get-pants --bin-dir .
endif


## Packages and installs the python packages.
install-python-components: pants
	./pants package ::
	python3 -m pip install dist/*.whl --force-reinstall


## Publishes java packages to maven local.
install-java-components:
	cd codegen && ./gradlew publishToMavenLocal


## Installs java and python components locally.
install-components: install-python-components install-java-components


## Builds the Java code generation packages.
smithy-build:
	cd codegen && ./gradlew clean build


## Generates the protocol tests, rebuilding necessary Java packages.
generate-protocol-tests:
	cd codegen && ./gradlew clean :smithy-python-protocol-test:build


## Runs already-generated protocol tests.
run-protocol-tests:
	cd codegen/smithy-python-protocol-test/build/smithyprojections/smithy-python-protocol-test/rest-json-1/python-client-codegen && \
	python3 -m pip install '.[tests]' && \
	python3 -m pytest tests


## Generates and runs protocol tests.
test-protocols: install-python-components generate-protocol-tests run-protocol-tests


## Runs formatters/fixers/linters for the python packages.
lint-py: pants
	./pants fix lint python-packages/smithy-python::
	./pants fix lint python-packages/aws-smithy-python::


## Runs checkers for the python packages.
check-py: pants
	./pants check python-packages/smithy-python::
	./pants check python-packages/aws-smithy-python::


## Runs tests for the python packages.
test-py: pants
	./pants test python-packages/smithy-python::
	./pants test python-packages/aws-smithy-python::


## Runs formatters/fixers/linters/checkers/tests for the python packages.
build-py: lint-py check-py test-py


## Clean up generated code, artifacts, and remove pants.
clean:
	rm -rf pants dist/
	cd codegen && ./gradlew clean
