from __future__ import annotations

from typing import Unpack, overload

from smithy_core.aio.client import AsyncClient
from smithy_http.plugins import user_agent_plugin

from endpoint_rules_client import models
from endpoint_rules_client.aio.config import AsyncConfig, Plugin


class AsyncEndpointService(AsyncClient[AsyncConfig]):
    "A service whose endpoint rules read config, input, and operation values."

    _client_plugins = (user_agent_plugin,)

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
        Invokes the Ping operation.

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
        Invokes the PutThing operation.

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

    def _new_config(self) -> AsyncConfig:
        return AsyncConfig()
