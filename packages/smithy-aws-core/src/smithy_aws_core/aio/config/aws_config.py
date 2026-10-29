# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypedDict, Unpack

from smithy_core.aio._program import run_program_async
from smithy_core.retries import RetryStrategyOptions, RetryStrategyType

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import AsyncClientTransport
    from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
    from smithy_core.aio.interfaces.retries import AsyncRetryStrategy
    from smithy_core.interfaces import URI
    from smithy_http.interfaces import HTTPRequestConfiguration

    from smithy_aws_core.identity.components import (
        AWSCredentialsIdentity,
        AWSIdentityProperties,
    )

from ...config.aws_config import (
    _AwsConfigBase,  # pyright: ignore[reportPrivateUsage]
    _base_fields,  # pyright: ignore[reportPrivateUsage]
)
from ...config.types import ConfigSource, FieldSpec
from .context import AsyncSharedConfigContext
from .filesystem import AsyncFileSystem
from .resolvers import (
    resolve_endpoint_uri,
    resolve_max_attempts,
    resolve_region,
    resolve_retry_mode,
    resolve_sdk_ua_app_id,
)


class AwsConfigOverrides(TypedDict, total=False):
    """Common keyword overrides accepted by AWS config resolution."""

    region: str | None
    retry_mode: RetryStrategyType | None
    max_attempts: int | None
    endpoint_uri: "str | URI | None"
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    aws_credentials_identity_resolver: (
        "AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None"
    )
    sdk_ua_app_id: str | None
    user_agent_extra: str | None
    interceptors: list[Any]
    http_request_config: "HTTPRequestConfiguration | None"
    transport: "AsyncClientTransport[Any, Any] | None"
    retry_strategy: "AsyncRetryStrategy | RetryStrategyOptions | None"


@dataclass(kw_only=True, init=False, repr=False)
class AsyncAwsConfig(_AwsConfigBase):
    """Base configuration class for all AWS services.

    Fields are resolved asynchronously from multiple sources (env vars,
    config files, defaults) through the resolve() classmethod.

    Do not instantiate directly — use:
        config = await AsyncAwsConfig.resolve()
    """

    region: str | None = None
    """The AWS region to connect to.
    """

    retry_mode: RetryStrategyType | None = None
    """The retry mode to use. Accepted overrides are ``standard`` and ``adaptive``.

    ``legacy`` is rejected when set here; when it comes from the environment or a
    config file it warns and falls back to ``standard``.
    """

    max_attempts: int | None = None
    """The maximum number of attempts to make per request, including the initial
    attempt. Must be an integer of at least 1."""

    endpoint_uri: "str | URI | None" = None
    """A static URI to route requests to."""

    aws_access_key_id: str | None = field(default=None, repr=False)
    """The identifier for a secret access key.

    Set this together with ``aws_secret_access_key`` to supply credentials in
    code. Cannot be modified after resolution; see
    ``aws_credentials_identity_resolver`` to supply credentials dynamically.
    """

    aws_secret_access_key: str | None = field(default=None, repr=False)
    """A secret access key that can be used to sign requests.

    Must be set together with ``aws_access_key_id``.
    """

    aws_session_token: str | None = field(default=None, repr=False)
    """The session token used with temporary AWS credentials.

    Set this together with ``aws_access_key_id`` and ``aws_secret_access_key``
    when supplying temporary credentials in code.
    """

    aws_credentials_identity_resolver: "AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None" = None
    """Resolves AWS Credentials.

    Set automatically to a ``StaticCredentialsResolver`` when
    ``aws_access_key_id`` and ``aws_secret_access_key`` are supplied in code.
    """

    sdk_ua_app_id: str | None = None
    """A unique and opaque application ID that is appended to the User-Agent
    header."""

    user_agent_extra: str | None = None
    """Additional suffix to be added to the User-Agent header."""

    interceptors: list[Any] = field(default_factory=list)  # type: ignore
    """The list of interceptors, which are hooks that are called during the
    execution of a request."""

    http_request_config: "HTTPRequestConfiguration | None" = None
    """Configuration for individual HTTP requests."""

    transport: "AsyncClientTransport[Any, Any] | None" = None
    """The transport to use to send requests"""

    retry_strategy: Any | None = None
    """The retry strategy or options for configuring retry behavior.
    """

    _ctx: AsyncSharedConfigContext | None = field(
        default=None, repr=False, compare=False
    )
    _sources: dict[str, ConfigSource] = field(  # type: ignore[assignment]
        default_factory=dict,
        repr=False,
        compare=False,
    )

    _FIELDS: ClassVar[dict[str, FieldSpec]] = _base_fields(
        resolve_region=resolve_region,
        resolve_retry_mode=resolve_retry_mode,
        resolve_max_attempts=resolve_max_attempts,
        resolve_endpoint_uri=resolve_endpoint_uri,
        resolve_sdk_ua_app_id=resolve_sdk_ua_app_id,
    )
    _RESOLVE_PREFIX: ClassVar[str] = "await "

    @classmethod
    async def resolve(
        cls,
        *,
        profile: str | None = None,
        fs: AsyncFileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[AwsConfigOverrides],
    ) -> Self:
        """Resolve a config object from environment, config files, and defaults.

        This is the only supported way to create a config instance.

        :param profile: Override the active profile name.
        :param fs: Override the filesystem abstraction.
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        :raises ProfileNotFoundError: If a profile is requested via ``profile`` or
            the ``AWS_PROFILE`` environment variable but is not defined in the
            config files.
        """
        return await cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )

    @classmethod
    async def _resolve(
        cls,
        *,
        profile: str | None,
        fs: AsyncFileSystem | None,
        config_file_path: str | None,
        credentials_file_path: str | None,
        overrides: Mapping[str, object],
    ) -> Self:
        """Internal resolution entry point for generated typed config factories."""
        return await run_program_async(
            cls._resolve_program(
                profile=profile,
                fs=fs,
                config_file_path=config_file_path,
                credentials_file_path=credentials_file_path,
                overrides=overrides,
            )
        )

    def resolution_context(self) -> AsyncSharedConfigContext | None:
        """Get the resolution context used to create this config.

        :returns: The AsyncSharedConfigContext, or None if not available.
        """
        return self._ctx

    @classmethod
    def _new_context(cls, **kwargs: Any) -> AsyncSharedConfigContext:
        return AsyncSharedConfigContext(**kwargs)

    def _static_credentials_resolver(self, identity: "AWSCredentialsIdentity") -> Any:
        from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver

        return AsyncStaticCredentialsResolver(identity=identity)
