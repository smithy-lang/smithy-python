#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import warnings
from datetime import UTC, datetime

from smithy_core import URI
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_core.exceptions import SmithyIdentityError
from smithy_http import Field, Fields, HTTPRequest
from smithy_http.aio.interfaces import AsyncHTTPClient

from ... import __version__
from ...identity.components import AWSCredentialsIdentity, AWSIdentityProperties
from ...identity.imds import Config, Token

_USER_AGENT_FIELD = Field(
    name="User-Agent",
    values=[f"aws-sdk-python-imds-client/{__version__}"],
)


class AsyncTokenCache:
    """Holds the token needed to fetch instance metadata.

    In addition, it knows how to refresh itself.
    """

    _TOKEN_PATH = "/latest/api/token"  # noqa: S105

    def __init__(self, http_client: AsyncHTTPClient, config: Config):
        self._http_client = http_client
        self._config = config
        self._base_uri = config.endpoint_uri
        self._refresh_lock = asyncio.Lock()
        self._token = None

    async def get_token(self) -> Token:
        """Return the cached IMDS session token, refreshing it when needed."""
        if self._should_refresh():
            await self._refresh()
        assert self._token is not None  # noqa: S101
        return self._token

    def _should_refresh(self) -> bool:
        return self._token is None or self._token.is_expired()

    async def _refresh(self) -> None:
        async with self._refresh_lock:
            if not self._should_refresh():
                return
            headers = Fields(
                [
                    _USER_AGENT_FIELD,
                    Field(
                        name="x-aws-ec2-metadata-token-ttl-seconds",
                        values=[str(self._config.token_ttl)],
                    ),
                ]
            )
            request = HTTPRequest(
                method="PUT",
                destination=URI(
                    scheme=self._base_uri.scheme,
                    host=self._base_uri.host,
                    port=self._base_uri.port,
                    path=self._TOKEN_PATH,
                ),
                fields=headers,
            )
            response = await self._http_client.send(request)
            token_value = await read_streaming_blob_async(response.body)
            self._token = Token(token_value.decode("utf-8"), self._config.token_ttl)


class AsyncEC2Metadata:
    """Client for the EC2 Instance Metadata Service (IMDSv2)."""

    def __init__(self, http_client: AsyncHTTPClient, config: Config | None = None):
        self._http_client = http_client
        self._config = config or Config()
        self._token_cache = AsyncTokenCache(
            http_client=self._http_client, config=self._config
        )

    async def get(self, *, path: str) -> str:
        """Return the metadata value at ``path``."""
        token = await self._token_cache.get_token()
        headers = Fields(
            [
                _USER_AGENT_FIELD,
                Field(
                    name="x-aws-ec2-metadata-token",
                    values=[token.value],
                ),
            ]
        )
        request = HTTPRequest(
            method="GET",
            destination=URI(
                scheme=self._config.endpoint_uri.scheme,
                host=self._config.endpoint_uri.host,
                port=self._config.endpoint_uri.port,
                path=path,
            ),
            fields=headers,
        )
        response = await self._http_client.send(request=request)
        body = await read_streaming_blob_async(response.body)
        return body.decode("utf-8")


class AsyncIMDSCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS Credentials from an EC2 Instance Metadata Service (IMDS) client.

    .. warning::
        This resolver is deprecated. Use the resolver provided by the
        ``aws-credentials-imds`` package instead.
    """

    _METADATA_PATH_BASE = "/latest/meta-data/iam/security-credentials"

    def __init__(self, http_client: AsyncHTTPClient, config: Config | None = None):
        warnings.warn(
            "`AsyncIMDSCredentialsResolver` is deprecated; install "
            "`aws-credentials-imds` and use its resolver instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # TODO: Respect IMDS specific config values from aws shared config file and environment.
        self._http_client = http_client
        self._ec2_metadata_client = AsyncEC2Metadata(
            http_client=http_client, config=config
        )
        self._config = config or Config()
        self._credentials = None
        self._profile_name = self._config.ec2_instance_profile_name

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        if (
            self._credentials is not None
            and self._credentials.expiration
            and datetime.now(UTC) < self._credentials.expiration
        ):
            return self._credentials

        profile = self._profile_name
        if profile is None:
            profile = await self._ec2_metadata_client.get(path=self._METADATA_PATH_BASE)

        creds_str = await self._ec2_metadata_client.get(
            path=f"{self._METADATA_PATH_BASE}/{profile}"
        )
        creds = json.loads(creds_str)

        access_key_id = creds.get("AccessKeyId")
        secret_access_key = creds.get("SecretAccessKey")
        session_token = creds.get("Token")
        account_id = creds.get("AccountId")
        expiration = creds.get("Expiration")
        if expiration is not None:
            expiration = datetime.fromisoformat(expiration).replace(tzinfo=UTC)

        if access_key_id is None or secret_access_key is None:
            raise SmithyIdentityError("AccessKeyId and SecretAccessKey are required")

        self._credentials = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            expiration=expiration,
            account_id=account_id,
        )
        return self._credentials

    async def invalidate(self) -> None:
        """Discard cached credentials so the next resolution re-queries IMDS."""
        self._credentials = None
