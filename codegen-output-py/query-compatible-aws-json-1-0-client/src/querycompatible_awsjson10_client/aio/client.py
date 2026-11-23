from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from querycompatible_awsjson10_client import models
from querycompatible_awsjson10_client.aio.config import (
    AsyncQueryCompatibleJSONRPC10Config,
    Plugin,
)
from querycompatible_awsjson10_client.aio.user_agent import aws_user_agent_plugin


class AsyncQueryCompatibleJSONRPC10Client(
    AsyncClient[AsyncQueryCompatibleJSONRPC10Config]
):
    "Client for QueryCompatibleJsonRpc10."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def query_compatible_operation(
        self,
        request: models.QueryCompatibleOperationInput
        | models.QueryCompatibleOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryCompatibleOperationOutput: ...

    @overload
    async def query_compatible_operation(
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

    async def query_compatible_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryCompatibleOperationOutput:
        return await self._invoke(
            self._select_input(models.QUERY_COMPATIBLE_OPERATION, args, kwargs),
            models.QUERY_COMPATIBLE_OPERATION,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncQueryCompatibleJSONRPC10Config:
        return await AsyncQueryCompatibleJSONRPC10Config.resolve()

    async def _post_setup(self, config: AsyncQueryCompatibleJSONRPC10Config) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_context = config.resolution_context()
            config_file = None
            profile_name = None
            if config_context is not None:
                config_file = await config_context.parsed_profiles()
                if config_context.profile_source is ConfigSource.OVERRIDE:
                    profile_name = config_context.profile_name
            config.aws_credentials_identity_resolver = await AsyncIdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(AsyncHTTPClient | None, config.transport),
            )
