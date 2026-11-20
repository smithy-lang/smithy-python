from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from aws_sigv4_client import models
from aws_sigv4_client.config import FieldNotesConfig, Plugin
from aws_sigv4_client.user_agent import aws_user_agent_plugin


class FieldNotesClient(Client[FieldNotesConfig]):
    "An AWS service that signs requests with SigV4."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

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
    def put_note(
        self,
        request: models.PutNoteInput | models.PutNoteInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutNoteOutput: ...

    @overload
    def put_note(
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

    def put_note(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutNoteOutput:
        return self._invoke(
            self._select_input(models.PUT_NOTE, args, kwargs),
            models.PUT_NOTE,
            [],
            plugins,
        )

    def _new_config(self) -> FieldNotesConfig:
        return FieldNotesConfig.resolve()

    def _post_setup(self, config: FieldNotesConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_context = config.resolution_context()
            config_file = None
            profile_name = None
            if config_context is not None:
                config_file = config_context.parsed_profiles()
                if config_context.profile_source is ConfigSource.OVERRIDE:
                    profile_name = config_context.profile_name
            config.aws_credentials_identity_resolver = IdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(HTTPClient | None, config.transport),
            )
