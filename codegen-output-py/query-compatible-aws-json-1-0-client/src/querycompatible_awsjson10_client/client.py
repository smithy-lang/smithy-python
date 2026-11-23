from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from querycompatible_awsjson10_client import models
from querycompatible_awsjson10_client.config import (
    Plugin,
    QueryCompatibleJSONRPC10Config,
)
from querycompatible_awsjson10_client.user_agent import aws_user_agent_plugin


class QueryCompatibleJSONRPC10Client(Client[QueryCompatibleJSONRPC10Config]):
    "Client for QueryCompatibleJsonRpc10."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    def query_compatible_operation(
        self,
        request: models.QueryCompatibleOperationInput
        | models.QueryCompatibleOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryCompatibleOperationOutput: ...

    @overload
    def query_compatible_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryCompatibleOperationInputDict],
    ) -> models.QueryCompatibleOperationOutput:
        """
        Invokes the QueryCompatibleOperation operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def query_compatible_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryCompatibleOperationOutput:
        return self._invoke(
            self._select_input(models.QUERY_COMPATIBLE_OPERATION, args, kwargs),
            models.QUERY_COMPATIBLE_OPERATION,
            [],
            plugins,
        )

    def _new_config(self) -> QueryCompatibleJSONRPC10Config:
        return QueryCompatibleJSONRPC10Config.resolve()

    def _post_setup(self, config: QueryCompatibleJSONRPC10Config) -> None:
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
