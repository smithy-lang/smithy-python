from __future__ import annotations

from typing import Unpack, overload

from smithy_core.client import Client
from smithy_http.plugins import user_agent_plugin

from endpoint_rules_client import models
from endpoint_rules_client.config import Config, Plugin


class EndpointService(Client[Config]):
    "A service whose endpoint rules read config, input, and operation values."

    _client_plugins = (user_agent_plugin,)

    @overload
    def ping(
        self,
        request: models.PingInput | models.PingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PingOutput: ...

    @overload
    def ping(
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

    def ping(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PingOutput:
        return self._invoke(
            self._select_input(models.PING, args, kwargs),
            models.PING,
            [],
            plugins,
        )

    @overload
    def put_thing(
        self,
        request: models.PutThingInput | models.PutThingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutThingOutput: ...

    @overload
    def put_thing(
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

    def put_thing(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutThingOutput:
        return self._invoke(
            self._select_input(models.PUT_THING, args, kwargs),
            models.PUT_THING,
            [],
            plugins,
        )

    def _new_config(self) -> Config:
        return Config()
