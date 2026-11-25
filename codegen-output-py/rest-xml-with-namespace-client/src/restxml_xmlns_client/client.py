from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from restxml_xmlns_client import models
from restxml_xmlns_client.config import Plugin, RestXmlProtocolNamespaceConfig
from restxml_xmlns_client.user_agent import aws_user_agent_plugin


class RestXmlProtocolNamespaceClient(Client[RestXmlProtocolNamespaceConfig]):
    """
    A REST XML service that sends XML requests and responses.

    This service and test case is complementary to the test cases
    in the `restXml` directory, but the service under test here has
    the `xmlNamespace` trait applied to it.

    See https://github.com/smithy-lang/smithy/issues/616
    """

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    def simple_scalar_properties(
        self,
        request: models.SimpleScalarPropertiesInput
        | models.SimpleScalarPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarPropertiesOutput: ...

    @overload
    def simple_scalar_properties(
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

    def simple_scalar_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarPropertiesOutput:
        return self._invoke(
            self._select_input(models.SIMPLE_SCALAR_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_PROPERTIES,
            [],
            plugins,
        )

    def _new_config(self) -> RestXmlProtocolNamespaceConfig:
        return RestXmlProtocolNamespaceConfig.resolve()

    def _post_setup(self, config: RestXmlProtocolNamespaceConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_file, profile_name = self._profile_overrides(config)
            config.aws_credentials_identity_resolver = IdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(HTTPClient | None, config.transport),
            )

    def _profile_overrides(
        self, config: RestXmlProtocolNamespaceConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
