from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from features_client import models
from features_client.config import FieldNotesConfig, Plugin
from features_client.user_agent import aws_user_agent_plugin


class FieldNotesClient(Client[FieldNotesConfig]):
    """
    An AWS service that uses every client feature the generator supports.

    Its endpoint rules read config, input, and operation values. Its
    operations
    use SigV4, API key auth, optional auth, and no auth.
    """

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    def echo(
        self,
        request: models.EchoInput | models.EchoInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EchoOutput: ...

    @overload
    def echo(
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

    def echo(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EchoOutput:
        return self._invoke(
            self._select_input(models.ECHO, args, kwargs),
            models.ECHO,
            [],
            plugins,
        )

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
        Uses API key auth.

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
        Needs no auth.

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
        Needs no auth.

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
