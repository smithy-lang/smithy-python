from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_core.aio.pagination import AsyncItemPaginator
from smithy_http.aio.identity.token import AsyncStaticTokenResolver
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.identity import TokenIdentity
from smithy_http.plugins import user_agent_plugin

from features_client import models
from features_client.aio.config import AsyncFieldNotesConfig, Plugin
from features_client.aio.user_agent import aws_user_agent_plugin


class AsyncFieldNotesClient(AsyncClient[AsyncFieldNotesConfig]):
    """
    An AWS service that uses every client feature the generator supports.

    Its endpoint rules read config, input, and operation values. Its
    operations
    use SigV4, bearer token auth, API key auth, optional auth, and no auth.
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
    async def get_note(
        self,
        request: models.GetNoteInput | models.GetNoteInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GetNoteOutput: ...

    @overload
    async def get_note(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GetNoteInputDict],
    ) -> models.GetNoteOutput:
        """
        Reads a note, with a bearer token.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def get_note(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GetNoteOutput:
        return await self._invoke(
            self._select_input(models.GET_NOTE, args, kwargs),
            models.GET_NOTE,
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
    async def list_notes(
        self,
        request: models.ListNotesInput | models.ListNotesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ListNotesOutput: ...

    @overload
    async def list_notes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ListNotesInputDict],
    ) -> models.ListNotesOutput:
        """
        Lists notes a page at a time. Needs no auth.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def list_notes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ListNotesOutput:
        return await self._invoke(
            self._select_input(models.LIST_NOTES, args, kwargs),
            models.LIST_NOTES,
            [],
            plugins,
        )

    @overload
    def paginate_list_notes(
        self,
        request: models.ListNotesInput | models.ListNotesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
        stop_on_same_token: bool = True,
    ) -> AsyncItemPaginator[models.ListNotesOutput, str]: ...

    @overload
    def paginate_list_notes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        stop_on_same_token: bool = True,
        **kwargs: Unpack[models.ListNotesInputDict],
    ) -> AsyncItemPaginator[models.ListNotesOutput, str]:
        """
        Iterates the pages of the ListNotes operation.

        Each page is the output of one call, sent as iteration reaches it. The
        request's token starts the first page. Pagination ends at a page with no
        token or an empty one. By default, it also ends, normally, at a page
        whose token equals the one its request sent, including the starting
        token. ``items()`` iterates the items of each page instead.

        :param plugins: Callables that change the configuration for each call of
        this traversal only.
        :param stop_on_same_token: Whether to end pagination at a page whose
        token equals, by value, the one its request sent. Set to False to keep
        requesting pages when tokens repeat, such as when polling for new
        results. A page with no token, or an empty one, still ends pagination.
        This option is not sent to the service.
        """

    def paginate_list_notes(
        self,
        /,
        *args: object,
        plugins: list[Plugin] | None = None,
        stop_on_same_token: bool = True,
        **kwargs: object,
    ) -> AsyncItemPaginator[models.ListNotesOutput, str]:
        return AsyncItemPaginator(
            self._build_input(
                self._select_input(models.LIST_NOTES, args, kwargs),
                models.LIST_NOTES,
            ),
            self.list_notes,
            plugins,
            input_token="next_token",  # noqa: S106 - a member name, not a secret
            output_token=("next_token",),
            items=("items",),
            stop_on_same_token=stop_on_same_token,
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
            config_file, profile_name = await self._profile_overrides(config)
            config.aws_credentials_identity_resolver = await AsyncIdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(AsyncHTTPClient | None, config.transport),
            )

        if config.token_identity_resolver is None:
            if config.token is not None:
                config.token_identity_resolver = AsyncStaticTokenResolver()
            else:
                config_file, profile_name = await self._profile_overrides(config)
                config.token_identity_resolver = await AsyncIdentityChain.create(
                    TokenIdentity,
                    config_file=config_file,
                    profile_name=profile_name,
                    region_override=config.region,
                    http_client=cast(AsyncHTTPClient | None, config.transport),
                )

    async def _profile_overrides(
        self, config: AsyncFieldNotesConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = await config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
