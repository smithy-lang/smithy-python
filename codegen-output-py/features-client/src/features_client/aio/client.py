from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from features_client import models
from features_client.aio.config import AsyncFieldNotesConfig, Plugin
from features_client.aio.user_agent import aws_user_agent_plugin


class AsyncFieldNotesClient(AsyncClient[AsyncFieldNotesConfig]):
    """
    An AWS service that uses every client feature the generator supports.

    Its endpoint rules read config, input, and operation values. Its
    operations
    use SigV4, API key auth, optional auth, and no auth.
    """

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def echo(
        self,
        request: models.EchoInput | models.EchoInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EchoOutput: ...

    @overload
    async def echo(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EchoInputDict],
    ) -> models.EchoOutput:
        """
        Uses API key auth, but sends no key when it has none.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def echo(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EchoOutput:
        return await self._invoke(
            self._select_input(models.ECHO, args, kwargs),
            models.ECHO,
            [],
            plugins,
        )

    @overload
    async def get_thing(
        self,
        request: models.GetThingInput | models.GetThingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GetThingOutput: ...

    @overload
    async def get_thing(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GetThingInputDict],
    ) -> models.GetThingOutput:
        """
        Uses API key auth.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def get_thing(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GetThingOutput:
        return await self._invoke(
            self._select_input(models.GET_THING, args, kwargs),
            models.GET_THING,
            [],
            plugins,
        )

    @overload
    async def ping(
        self,
        request: models.PingInput | models.PingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PingOutput: ...

    @overload
    async def ping(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PingInputDict],
    ) -> models.PingOutput:
        """
        Needs no auth.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def ping(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PingOutput:
        return await self._invoke(
            self._select_input(models.PING, args, kwargs),
            models.PING,
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

    @overload
    async def put_thing(
        self,
        request: models.PutThingInput | models.PutThingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutThingOutput: ...

    @overload
    async def put_thing(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PutThingInputDict],
    ) -> models.PutThingOutput:
        """
        Needs no auth.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def put_thing(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutThingOutput:
        return await self._invoke(
            self._select_input(models.PUT_THING, args, kwargs),
            models.PUT_THING,
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
