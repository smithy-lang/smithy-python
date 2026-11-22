from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from awsjson10_client import models
from awsjson10_client.config import JSONRPC10Config, Plugin
from awsjson10_client.user_agent import aws_user_agent_plugin


class JSONRPC10Client(Client[JSONRPC10Config]):
    "Client for JsonRpc10."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    def content_type_parameters(
        self,
        request: models.ContentTypeParametersInput
        | models.ContentTypeParametersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ContentTypeParametersOutput: ...

    @overload
    def content_type_parameters(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ContentTypeParametersInputDict],
    ) -> models.ContentTypeParametersOutput:
        """
        The example tests how servers must support requests
        containing a `Content-Type` header with parameters.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def content_type_parameters(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ContentTypeParametersOutput:
        return self._invoke(
            self._select_input(models.CONTENT_TYPE_PARAMETERS, args, kwargs),
            models.CONTENT_TYPE_PARAMETERS,
            [],
            plugins,
        )

    @overload
    def empty_input_and_empty_output(
        self,
        request: models.EmptyInputAndEmptyOutputInput
        | models.EmptyInputAndEmptyOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EmptyInputAndEmptyOutputOutput: ...

    @overload
    def empty_input_and_empty_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EmptyInputAndEmptyOutputInputDict],
    ) -> models.EmptyInputAndEmptyOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has an empty input
        and empty output structure that reuses the same shape. While this should
        be rare, code generators must support this.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def empty_input_and_empty_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EmptyInputAndEmptyOutputOutput:
        return self._invoke(
            self._select_input(models.EMPTY_INPUT_AND_EMPTY_OUTPUT, args, kwargs),
            models.EMPTY_INPUT_AND_EMPTY_OUTPUT,
            [],
            plugins,
        )

    @overload
    def endpoint_operation(
        self,
        request: models.EndpointOperationInput | models.EndpointOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointOperationOutput: ...

    @overload
    def endpoint_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EndpointOperationInputDict],
    ) -> models.EndpointOperationOutput:
        """
        Invokes the EndpointOperation operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def endpoint_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointOperationOutput:
        return self._invoke(
            self._select_input(models.ENDPOINT_OPERATION, args, kwargs),
            models.ENDPOINT_OPERATION,
            [],
            plugins,
        )

    @overload
    def endpoint_with_host_label_operation(
        self,
        request: models.EndpointWithHostLabelOperationInput
        | models.EndpointWithHostLabelOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointWithHostLabelOperationOutput: ...

    @overload
    def endpoint_with_host_label_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EndpointWithHostLabelOperationInputDict],
    ) -> models.EndpointWithHostLabelOperationOutput:
        """
        Invokes the EndpointWithHostLabelOperation operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def endpoint_with_host_label_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointWithHostLabelOperationOutput:
        return self._invoke(
            self._select_input(models.ENDPOINT_WITH_HOST_LABEL_OPERATION, args, kwargs),
            models.ENDPOINT_WITH_HOST_LABEL_OPERATION,
            [],
            plugins,
        )

    @overload
    def greeting_with_errors(
        self,
        request: models.GreetingWithErrorsInput | models.GreetingWithErrorsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GreetingWithErrorsOutput: ...

    @overload
    def greeting_with_errors(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GreetingWithErrorsInputDict],
    ) -> models.GreetingWithErrorsOutput:
        """
        This operation has three possible return values:

        1. A successful response in the form of GreetingWithErrorsOutput
        2. An InvalidGreeting error.
        3. A ComplexError error.

        Implementations must be able to successfully take a response and
        properly deserialize successful and error responses.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def greeting_with_errors(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GreetingWithErrorsOutput:
        return self._invoke(
            self._select_input(models.GREETING_WITH_ERRORS, args, kwargs),
            models.GREETING_WITH_ERRORS,
            [],
            plugins,
        )

    @overload
    def host_with_path_operation(
        self,
        request: models.HostWithPathOperationInput
        | models.HostWithPathOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HostWithPathOperationOutput: ...

    @overload
    def host_with_path_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HostWithPathOperationInputDict],
    ) -> models.HostWithPathOperationOutput:
        """
        Invokes the HostWithPathOperation operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def host_with_path_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HostWithPathOperationOutput:
        return self._invoke(
            self._select_input(models.HOST_WITH_PATH_OPERATION, args, kwargs),
            models.HOST_WITH_PATH_OPERATION,
            [],
            plugins,
        )

    @overload
    def json_unions(
        self,
        request: models.JsonUnionsInput | models.JsonUnionsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonUnionsOutput: ...

    @overload
    def json_unions(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonUnionsInputDict],
    ) -> models.JsonUnionsOutput:
        """
        This operation uses unions for inputs and outputs.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def json_unions(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonUnionsOutput:
        return self._invoke(
            self._select_input(models.JSON_UNIONS, args, kwargs),
            models.JSON_UNIONS,
            [],
            plugins,
        )

    @overload
    def no_input_and_no_output(
        self,
        request: models.NoInputAndNoOutputInput | models.NoInputAndNoOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndNoOutputOutput: ...

    @overload
    def no_input_and_no_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndNoOutputInputDict],
    ) -> models.NoInputAndNoOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input or
        output.
        While this should be rare, code generators must support this.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def no_input_and_no_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndNoOutputOutput:
        return self._invoke(
            self._select_input(models.NO_INPUT_AND_NO_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_NO_OUTPUT,
            [],
            plugins,
        )

    @overload
    def no_input_and_output(
        self,
        request: models.NoInputAndOutputInput | models.NoInputAndOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndOutputOutput: ...

    @overload
    def no_input_and_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndOutputInputDict],
    ) -> models.NoInputAndOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input and
        the
        output is empty. While this should be rare, code generators must support
        this.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def no_input_and_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndOutputOutput:
        return self._invoke(
            self._select_input(models.NO_INPUT_AND_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_OUTPUT,
            [],
            plugins,
        )

    @overload
    def operation_with_defaults(
        self,
        request: models.OperationWithDefaultsInput
        | models.OperationWithDefaultsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithDefaultsOutput: ...

    @overload
    def operation_with_defaults(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithDefaultsInputDict],
    ) -> models.OperationWithDefaultsOutput:
        """
        Invokes the OperationWithDefaults operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def operation_with_defaults(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithDefaultsOutput:
        return self._invoke(
            self._select_input(models.OPERATION_WITH_DEFAULTS, args, kwargs),
            models.OPERATION_WITH_DEFAULTS,
            [],
            plugins,
        )

    @overload
    def operation_with_nested_structure(
        self,
        request: models.OperationWithNestedStructureInput
        | models.OperationWithNestedStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithNestedStructureOutput: ...

    @overload
    def operation_with_nested_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithNestedStructureInputDict],
    ) -> models.OperationWithNestedStructureOutput:
        """
        Invokes the OperationWithNestedStructure operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def operation_with_nested_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithNestedStructureOutput:
        return self._invoke(
            self._select_input(models.OPERATION_WITH_NESTED_STRUCTURE, args, kwargs),
            models.OPERATION_WITH_NESTED_STRUCTURE,
            [],
            plugins,
        )

    @overload
    def operation_with_required_members(
        self,
        request: models.OperationWithRequiredMembersInput
        | models.OperationWithRequiredMembersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithRequiredMembersOutput: ...

    @overload
    def operation_with_required_members(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithRequiredMembersInputDict],
    ) -> models.OperationWithRequiredMembersOutput:
        """
        Invokes the OperationWithRequiredMembers operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def operation_with_required_members(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithRequiredMembersOutput:
        return self._invoke(
            self._select_input(models.OPERATION_WITH_REQUIRED_MEMBERS, args, kwargs),
            models.OPERATION_WITH_REQUIRED_MEMBERS,
            [],
            plugins,
        )

    @overload
    def operation_with_required_members_with_defaults(
        self,
        request: models.OperationWithRequiredMembersWithDefaultsInput
        | models.OperationWithRequiredMembersWithDefaultsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithRequiredMembersWithDefaultsOutput: ...

    @overload
    def operation_with_required_members_with_defaults(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithRequiredMembersWithDefaultsInputDict],
    ) -> models.OperationWithRequiredMembersWithDefaultsOutput:
        """
        Invokes the OperationWithRequiredMembersWithDefaults operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def operation_with_required_members_with_defaults(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithRequiredMembersWithDefaultsOutput:
        return self._invoke(
            self._select_input(
                models.OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS, args, kwargs
            ),
            models.OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS,
            [],
            plugins,
        )

    @overload
    def put_with_content_encoding(
        self,
        request: models.PutWithContentEncodingInput
        | models.PutWithContentEncodingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutWithContentEncodingOutput: ...

    @overload
    def put_with_content_encoding(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PutWithContentEncodingInputDict],
    ) -> models.PutWithContentEncodingOutput:
        """
        Invokes the PutWithContentEncoding operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def put_with_content_encoding(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutWithContentEncodingOutput:
        return self._invoke(
            self._select_input(models.PUT_WITH_CONTENT_ENCODING, args, kwargs),
            models.PUT_WITH_CONTENT_ENCODING,
            [],
            plugins,
        )

    @overload
    def query_incompatible_operation(
        self,
        request: models.QueryIncompatibleOperationInput
        | models.QueryIncompatibleOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryIncompatibleOperationOutput: ...

    @overload
    def query_incompatible_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryIncompatibleOperationInputDict],
    ) -> models.QueryIncompatibleOperationOutput:
        """
        Invokes the QueryIncompatibleOperation operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def query_incompatible_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryIncompatibleOperationOutput:
        return self._invoke(
            self._select_input(models.QUERY_INCOMPATIBLE_OPERATION, args, kwargs),
            models.QUERY_INCOMPATIBLE_OPERATION,
            [],
            plugins,
        )

    @overload
    def simple_scalar_properties(
        self,
        request: models.SimpleScalarPropertiesInput
        | models.SimpleScalarPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarPropertiesOutput: ...

    @overload
    def simple_scalar_properties(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleScalarPropertiesInputDict],
    ) -> models.SimpleScalarPropertiesOutput:
        """
        Invokes the SimpleScalarProperties operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def simple_scalar_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarPropertiesOutput:
        return self._invoke(
            self._select_input(models.SIMPLE_SCALAR_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_PROPERTIES,
            [],
            plugins,
        )

    def _new_config(self) -> JSONRPC10Config:
        return JSONRPC10Config.resolve()

    def _post_setup(self, config: JSONRPC10Config) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_context = config.resolution_context()
            config_file = None
            profile_name = None
            if config_context is not None:
                config_file = config_context.parsed_profiles()
                if config_context.profile_source is ConfigSource.OVERRIDE:
                    profile_name = config_context.profile_name
            config.aws_credentials_identity_resolver = IdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(HTTPClient | None, config.transport),
            )
