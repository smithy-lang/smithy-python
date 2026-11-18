from __future__ import annotations

from typing import Unpack, overload

from smithy_core.client import Client
from smithy_http.plugins import user_agent_plugin

from api_key_auth_client import models
from api_key_auth_client.config import Config, Plugin


class ApiKeyService(Client[Config]):
    "A service that authenticates with an API key."

    _client_plugins = (user_agent_plugin,)

    @overload
    def get_thing(
        self,
        request: models.GetThingInput | models.GetThingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GetThingOutput: ...

    @overload
    def get_thing(
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

    def get_thing(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GetThingOutput:
        return self._invoke(
            self._select_input(models.GET_THING, args, kwargs),
            models.GET_THING,
            [],
            plugins,
        )

    @overload
    def health(
        self,
        request: models.HealthInput | models.HealthInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HealthOutput: ...

    @overload
    def health(
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

    def health(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HealthOutput:
        return self._invoke(
            self._select_input(models.HEALTH, args, kwargs),
            models.HEALTH,
            [],
            plugins,
        )

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
        Sends the API key when it has one.

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

    def _new_config(self) -> Config:
        return Config()
