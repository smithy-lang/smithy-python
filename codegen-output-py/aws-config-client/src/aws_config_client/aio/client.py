from __future__ import annotations

from typing import Unpack, overload

from smithy_core.aio.client import AsyncClient
from smithy_http.plugins import user_agent_plugin

from aws_config_client import models
from aws_config_client.aio.config import AsyncWeatherStationConfig, Plugin
from aws_config_client.aio.user_agent import aws_user_agent_plugin


class AsyncWeatherStationClient(AsyncClient[AsyncWeatherStationConfig]):
    "An AWS service that reads its config from the environment and profiles."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def get_forecast(
        self,
        request: models.GetForecastInput | models.GetForecastInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GetForecastOutput: ...

    @overload
    async def get_forecast(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GetForecastInputDict],
    ) -> models.GetForecastOutput:
        """
        Gets the forecast for a city.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def get_forecast(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GetForecastOutput:
        return await self._invoke(
            self._select_input(models.GET_FORECAST, args, kwargs),
            models.GET_FORECAST,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncWeatherStationConfig:
        return await AsyncWeatherStationConfig.resolve()
