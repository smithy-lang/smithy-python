# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Self, Unpack

from smithy_core.aio.program import run_program_async

if TYPE_CHECKING:
    from aws_sdk_signers.interfaces.identity import AWSIdentityProperties
    from smithy_core.aio.interfaces import AsyncClientTransport
    from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

    from smithy_aws_core.identity.components import (
        AWSCredentialsIdentity,
    )

    type _AsyncTransport = AsyncClientTransport[Any, Any]
    type _AsyncCredentialsResolver = AsyncIdentityResolver[
        AWSCredentialsIdentity, AWSIdentityProperties
    ]

from ...config.aws_config import (
    _AwsConfigFields,  # pyright: ignore[reportPrivateUsage]
    _AwsConfigOverridesBase,  # pyright: ignore[reportPrivateUsage]
)
from .context import AsyncSharedConfigContext
from .filesystem import AsyncFileSystem


class AsyncAwsConfigOverrides(
    _AwsConfigOverridesBase[
        "_AsyncTransport",
        "_AsyncCredentialsResolver",
    ],
    total=False,
):
    """Common keyword overrides accepted by async AWS config resolution."""


@dataclass(kw_only=True, init=False, repr=False)
class AsyncAwsConfig(
    _AwsConfigFields[
        "_AsyncTransport",
        "_AsyncCredentialsResolver",
        AsyncSharedConfigContext,
    ]
):
    """Base configuration class for all AWS services.

    Fields are resolved asynchronously from multiple sources (env vars,
    config files, defaults) through the resolve() classmethod.

    Do not instantiate directly — use:
        config = await AsyncAwsConfig.resolve()
    """

    _RESOLVE_PREFIX: ClassVar[str] = "await "

    @classmethod
    async def resolve(
        cls,
        *,
        profile: str | None = None,
        fs: AsyncFileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[AsyncAwsConfigOverrides],
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

    @classmethod
    def _new_context(cls, **kwargs: Any) -> AsyncSharedConfigContext:
        return AsyncSharedConfigContext(**kwargs)

    def _static_credentials_resolver(self, identity: "AWSCredentialsIdentity") -> Any:
        from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver

        return AsyncStaticCredentialsResolver(identity=identity)
