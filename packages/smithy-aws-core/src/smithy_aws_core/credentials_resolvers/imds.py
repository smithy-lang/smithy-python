#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from typing import Literal

from smithy_core import URI
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties
from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import SimpleRetryStrategy
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.interfaces import HTTPClient

from .. import __version__
from ..identity import AWSCredentialsIdentity

_USER_AGENT_FIELD = Field(
    name="User-Agent",
    values=[f"aws-sdk-python-imds-client/{__version__}"],
)


@dataclass(init=False)
class Config:
    """Configuration for EC2Metadata."""

    _HOST_MAPPING = MappingProxyType(
        {"IPv4": "169.254.169.254", "IPv6": "[fd00:ec2::254]"}
    )
    _MIN_TTL = 5
    _MAX_TTL = 21600

    retry_strategy: RetryStrategy
    endpoint_uri: URI
    endpoint_mode: Literal["IPv4", "IPv6"]
    token_ttl: int

    def __init__(
        self,
        *,
        retry_strategy: RetryStrategy | None = None,
        endpoint_uri: URI | None = None,
        endpoint_mode: Literal["IPv4", "IPv6"] = "IPv4",
        token_ttl: int = _MAX_TTL,
        ec2_instance_profile_name: str | None = None,
    ):
        #  TODO: Implement retries.
        self.retry_strategy = retry_strategy or SimpleRetryStrategy(max_attempts=3)
        self.endpoint_mode = endpoint_mode
        self.endpoint_uri = self._resolve_endpoint(endpoint_uri, endpoint_mode)
        self.token_ttl = self._validate_token_ttl(token_ttl)
        self.ec2_instance_profile_name = ec2_instance_profile_name

    def _validate_token_ttl(self, ttl: int) -> int:
        if not self._MIN_TTL <= ttl <= self._MAX_TTL:
            raise ValueError(
                f"Token TTL must be between {self._MIN_TTL} and {self._MAX_TTL} seconds."
            )
        return ttl

    def _resolve_endpoint(
        self, endpoint_uri: URI | None, endpoint_mode: Literal["IPv4", "IPv6"]
    ) -> URI:
        if endpoint_uri is not None:
            return endpoint_uri

        return URI(
            scheme="http",
            host=self._HOST_MAPPING.get(endpoint_mode, self._HOST_MAPPING["IPv4"]),
            port=80,
        )


class Token:
    """Represents an IMDSv2 session token with a value and method for checking
    expiration."""

    def __init__(self, value: str, ttl: int):
        self._value = value
        self._ttl = ttl
        self._created_time = datetime.now()

    def is_expired(self) -> bool:
        return datetime.now() - self._created_time >= timedelta(seconds=self._ttl)

    @property
    def value(self) -> str:
        return self._value


class TokenCache:
    """Holds the token needed to fetch instance metadata.

    In addition, it knows how to refresh itself.
    """

    _TOKEN_PATH = "/latest/api/token"  # noqa: S105

    def __init__(self, http_client: HTTPClient, config: Config):
        self._http_client = http_client
        self._config = config
        self._base_uri = config.endpoint_uri
        self._refresh_lock = asyncio.Lock()
        self._token = None

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
            token_value = await response.consume_body_async()
            self._token = Token(token_value.decode("utf-8"), self._config.token_ttl)

    async def get_token(self) -> Token:
        if self._should_refresh():
            await self._refresh()
        assert self._token is not None  # noqa: S101
        return self._token


class EC2Metadata:
    def __init__(self, http_client: HTTPClient, config: Config | None = None):
        self._http_client = http_client
        self._config = config or Config()
        self._token_cache = TokenCache(
            http_client=self._http_client, config=self._config
        )

    async def get(self, *, path: str) -> str:
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
        body = await response.consume_body_async()
        return body.decode("utf-8")


class IMDSCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, IdentityProperties]
):
    """Resolves AWS Credentials from an EC2 Instance Metadata Service (IMDS) client."""

    _METADATA_PATH_BASE = "/latest/meta-data/iam/security-credentials"

    def __init__(self, http_client: HTTPClient, config: Config | None = None):
        # TODO: Respect IMDS specific config values from aws shared config file and environment.
        self._http_client = http_client
        self._ec2_metadata_client = EC2Metadata(http_client=http_client, config=config)
        self._config = config or Config()
        self._credentials = None
        self._profile_name = self._config.ec2_instance_profile_name

    async def get_identity(
        self, *, identity_properties: IdentityProperties
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
            raise SmithyIdentityException(
                "AccessKeyId and SecretAccessKey are required"
            )

        self._credentials = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            expiration=expiration,
            account_id=account_id,
        )
        return self._credentials
