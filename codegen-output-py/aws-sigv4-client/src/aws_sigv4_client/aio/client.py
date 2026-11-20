from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from aws_sigv4_client import models
from aws_sigv4_client.aio.config import AsyncFieldNotesConfig, Plugin
from aws_sigv4_client.aio.user_agent import aws_user_agent_plugin


class AsyncFieldNotesClient(AsyncClient[AsyncFieldNotesConfig]):
    "An AWS service that signs requests with SigV4."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def health(
        self,
        request: models.HealthInput | models.HealthInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HealthOutput: ...

    @overload
    async def health(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HealthInputDict],
    ) -> models.HealthOutput:
        """
        Needs no auth.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def health(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HealthOutput:
        return await self._invoke(
            self._select_input(models.HEALTH, args, kwargs),
            models.HEALTH,
            [],
            plugins,
        )

    @overload
    async def put_note(
        self,
        request: models.PutNoteInput | models.PutNoteInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutNoteOutput: ...

    @overload
    async def put_note(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PutNoteInputDict],
    ) -> models.PutNoteOutput:
        """
        Saves a note, signed with SigV4.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def put_note(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutNoteOutput:
        return await self._invoke(
            self._select_input(models.PUT_NOTE, args, kwargs),
            models.PUT_NOTE,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncFieldNotesConfig:
        return await AsyncFieldNotesConfig.resolve()

    async def _post_setup(self, config: AsyncFieldNotesConfig) -> None:
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
