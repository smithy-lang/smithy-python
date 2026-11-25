from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from restxml_xmlns_client import models
from restxml_xmlns_client.aio.config import AsyncRestXmlProtocolNamespaceConfig, Plugin
from restxml_xmlns_client.aio.user_agent import aws_user_agent_plugin


class AsyncRestXmlProtocolNamespaceClient(
    AsyncClient[AsyncRestXmlProtocolNamespaceConfig]
):
    """
    A REST XML service that sends XML requests and responses.

    This service and test case is complementary to the test cases
    in the `restXml` directory, but the service under test here has
    the `xmlNamespace` trait applied to it.

    See https://github.com/smithy-lang/smithy/issues/616
    """

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def simple_scalar_properties(
        self,
        request: models.SimpleScalarPropertiesInput
        | models.SimpleScalarPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarPropertiesOutput: ...

    @overload
    async def simple_scalar_properties(
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

    async def simple_scalar_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarPropertiesOutput:
        return await self._invoke(
            self._select_input(models.SIMPLE_SCALAR_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_PROPERTIES,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncRestXmlProtocolNamespaceConfig:
        return await AsyncRestXmlProtocolNamespaceConfig.resolve()

    async def _post_setup(self, config: AsyncRestXmlProtocolNamespaceConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_file, profile_name = await self._profile_overrides(config)
            config.aws_credentials_identity_resolver = await AsyncIdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(AsyncHTTPClient | None, config.transport),
            )

    async def _profile_overrides(
        self, config: AsyncRestXmlProtocolNamespaceConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = await config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
