from __future__ import annotations

from typing import Unpack, overload

from smithy_core.aio.client import AsyncClient
from smithy_http.plugins import user_agent_plugin

from api_key_auth_client import models
from api_key_auth_client.aio.config import AsyncConfig, Plugin


class AsyncApiKeyService(AsyncClient[AsyncConfig]):
    "A service that authenticates with an API key."

    _client_plugins = (user_agent_plugin,)

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
        Uses the service's API key auth.

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
        Sends the API key when it has one.

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

    def _new_config(self) -> AsyncConfig:
        return AsyncConfig()
