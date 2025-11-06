import asyncio
import configparser
import os
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, ClassVar, Literal

from smithy_core.aio.interfaces import (
    EndpointResolver,
)
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.interfaces import URI
from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import SimpleRetryStrategy
from smithy_http.interfaces import HTTPRequestConfiguration

from smithy_aws_core.identity import AWSCredentialsIdentity, AWSIdentityProperties

SOURCE_CONSTRUCTOR = "constructor"
SOURCE_ENVIRONMENT = "environment"
SOURCE_CREDENTIALS_FILE = "credentials_file"
SOURCE_CONFIG_FILE = "config_file"
SOURCE_DEFAULT = "default"
SOURCE_IN_CODE_UPDATE = "in_code_update"

SourceType = Literal[
    "constructor",
    "environment",
    "credentials_file",
    "config_file",
    "default",
    "in_code_update",
]


class ConfigValue:
    """Configuration value with metadata about its source"""

    def __init__(self, value: Any, source: SourceType):
        self.value = value
        self.source = source


class AWSClientConfig:
    """
    AWS Client Configuration with precedence-based resolution.

    The constructor uses explicit parameters with sentinel values (...) to provide
    IDE autocomplete while preserving precedence chain detection. The sentinel
    value (...) is Python's Ellipsis object, which allows us to distinguish
    between "not provided" vs "explicitly set to None".

    HOW TO ADD A NEW CONFIG FIELD:

    1. Add the parameter to the __init__ method with sentinel default:
       my_field: str | None = ...,  # type: ignore[assignment]

    2a. For standard resolution, add to CONFIG_FIELDS dictionary:
        "my_field": {
            "default": None,  # required
            "type": str | None,  # required - the expected type for type safety
            "env_var": "MY_ENV_VAR",  # optional environment variable name
            "config_key": "my_config_key",  # optional config/credentials file key
            "validator": "_validate_string"  # optional validation method
        }

    2b. For custom resolution, add to CONFIG_FIELDS dictionary AND a custom resolver method:
        "my_field": {
            "default": None,  # required
            "type": str | None,  # required - the expected type for type safety
            "validator": "_validate_string"  # optional validation method
            # Note: omit env_var and config_key since custom resolver handles resolution
        }

        async def _resolve_my_field(self, constructor_values, env_values,
                                    config_file_values, credentials_file_values,
                                    default_value, validator):
            # Custom resolution logic here
            return ConfigValue(resolved_value, source)

    3. Add property getter and setter:
       @property
       def my_field(self) -> str | None:
           return self._my_field.value

       @my_field.setter
       def my_field(self, value: str | None) -> None:
           self._my_field = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    4. If custom validation is needed, add a validator method:
       def _validate_my_field(self, value: Any, field_name: str) -> None:
           # Custom validation logic here
    """

    CONFIG_FIELDS: ClassVar[dict[str, dict[str, Any]]] = {
        "aws_credentials_identity_resolver": {
            "default": None,
            "type": IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
            | None,
        },
        "endpoint_resolver": {
            "default": None,
            "type": EndpointResolver | None,
        },
        "http_request_config": {
            "default": None,
            "type": HTTPRequestConfiguration | None,
        },
        "retry_strategy": {
            "default": SimpleRetryStrategy(),
            "type": RetryStrategy,
        },
        "aws_access_key_id": {
            "env_var": "AWS_ACCESS_KEY_ID",
            "config_key": "aws_access_key_id",
            "default": None,
            "type": str | None,
        },
        "aws_secret_access_key": {
            "env_var": "AWS_SECRET_ACCESS_KEY",
            "config_key": "aws_secret_access_key",
            "default": None,
            "type": str | None,
        },
        "aws_session_token": {
            "env_var": "AWS_SESSION_TOKEN",
            "config_key": "aws_session_token",
            "default": None,
            "type": str | None,
        },
        "endpoint_uri": {
            "env_var": "AWS_ENDPOINT_URL",
            "config_key": "endpoint_url",
            "default": None,
            "validator": "_validate_endpoint_uri",
        },
        "region": {
            "env_var": "AWS_REGION",
            "config_key": "region",
            "default": None,
            "type": str | None,
        },
        "sdk_ua_app_id": {
            "default": None,
            "type": str | None,
        },
        "user_agent_extra": {
            "default": None,
            "type": str | None,
        },
    }

    def __init__(
        self,
        *,
        aws_access_key_id: str | None = ...,  # type: ignore[assignment]
        aws_secret_access_key: str | None = ...,  # type: ignore[assignment]
        aws_session_token: str | None = ...,  # type: ignore[assignment]
        endpoint_uri: str | URI | None = ...,  # type: ignore[assignment]
        region: str | None = ...,  # type: ignore[assignment]
        sdk_ua_app_id: str | None = ...,  # type: ignore[assignment]
        user_agent_extra: str | None = ...,  # type: ignore[assignment]
        aws_credentials_identity_resolver: IdentityResolver[
            AWSCredentialsIdentity, AWSIdentityProperties
        ]
        | None = ...,  # type: ignore[assignment]
        endpoint_resolver: EndpointResolver | None = ...,  # type: ignore[assignment]
        http_request_config: HTTPRequestConfiguration | None = ...,  # type: ignore[assignment]
        retry_strategy: RetryStrategy = ...,  # type: ignore[assignment]
    ):
        self._constructor_values = {
            k: v for k, v in locals().items() if k != "self" and v is not ...
        }
        self._resolved = False

    async def resolve(
        self,
        *,
        environment_loader: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        config_file_loader: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        credentials_file_loader: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    ):
        """Resolve configuration from all sources

        Args:
            environment_loader: Custom environment loader function
            config_file_loader: Custom config file loader function
            credentials_file_loader: Custom credentials file loader function
        """

        if self._resolved:
            raise RuntimeError(
                "Config has already been resolved. Multiple calls to resolve() are not allowed."
            )

        env_task = (environment_loader or self._load_environment_values)()
        config_task = (config_file_loader or self._load_config_file_values)()
        creds_task = (credentials_file_loader or self._load_credentials_file_values)()

        env_values, config_file_values, credentials_file_values = await asyncio.gather(
            env_task, config_task, creds_task
        )

        for field_name, field_info in self.CONFIG_FIELDS.items():
            validator = field_info.get("validator")

            resolved_value = await self._resolve_field(
                field_name,
                self._constructor_values,
                env_values,
                config_file_values,
                credentials_file_values,
                field_info["default"],
                validator,
            )
            setattr(self, f"_{field_name}", resolved_value)

        self._resolved = True

    async def _load_environment_values(self) -> Mapping[str, str]:
        return os.environ

    # TODO: implement full config/credential file support
    async def _load_config_file_values(self) -> dict[str, Any]:
        def _read_config() -> dict[str, str]:
            config_path = Path.home() / ".aws" / "config"
            if not config_path.exists():
                return {}

            parser = configparser.ConfigParser()
            parser.read(config_path)

            profile = os.environ.get("AWS_PROFILE", "default")
            section_name = f"profile {profile}" if profile != "default" else "default"

            if section_name not in parser:
                return {}

            return dict(parser[section_name])

        return await asyncio.to_thread(_read_config)

    async def _load_credentials_file_values(self) -> dict[str, Any]:
        def _read_credentials() -> dict[str, str]:
            credentials_path = Path.home() / ".aws" / "credentials"
            if not credentials_path.exists():
                return {}

            parser = configparser.ConfigParser()
            parser.read(credentials_path)

            profile = os.environ.get("AWS_PROFILE", "default")

            if profile not in parser:
                return {}

            return dict(parser[profile])

        return await asyncio.to_thread(_read_credentials)

    async def _resolve_field(
        self,
        field_name: str,
        constructor_values: dict[str, Any],
        env_values: Mapping[str, Any],
        config_file_values: dict[str, Any],
        credentials_file_values: dict[str, Any],
        default_value: Any,
        validator: str | None,
    ) -> ConfigValue:
        custom_resolver = getattr(self, f"_resolve_{field_name}", None)
        if custom_resolver:
            return await custom_resolver(
                constructor_values,
                env_values,
                config_file_values,
                credentials_file_values,
                default_value,
                validator,
            )

        field_config = self.CONFIG_FIELDS.get(field_name, {})
        env_var = field_config.get("env_var")
        config_key = field_config.get("config_key")

        if field_name in constructor_values:
            value = constructor_values[field_name]  # type: ignore[reportUnknownVariableType]
            source = SOURCE_CONSTRUCTOR
        elif env_var and env_var in env_values:
            value = env_values[env_var]  # type: ignore[reportUnknownVariableType]
            source = SOURCE_ENVIRONMENT
        elif config_key and config_key in config_file_values:
            value = config_file_values[config_key]  # type: ignore[reportUnknownVariableType]
            source = SOURCE_CONFIG_FILE
        elif config_key and config_key in credentials_file_values:
            value = credentials_file_values[config_key]  # type: ignore[reportUnknownVariableType]
            source = SOURCE_CREDENTIALS_FILE
        else:
            value = default_value  # type: ignore[reportUnknownVariableType]
            source = SOURCE_DEFAULT

        if validator:
            getattr(self, validator)(value, field_name)
        else:
            expected_type = field_config["type"]

            # Skip type checking for protocol types (they can't be runtime checked)
            if self._is_protocol_type(expected_type):
                return ConfigValue(value, source)

            if not isinstance(value, expected_type):
                actual_name = type(value).__name__
                expected_name = getattr(expected_type, "__name__", str(expected_type))
                raise TypeError(
                    f"{field_name} must be {expected_name}, got {actual_name}"
                )

        return ConfigValue(value, source)

    def _is_protocol_type(self, type_hint: Any) -> bool:
        """Check if a type hint contains protocol types that can't be runtime checked"""
        if hasattr(type_hint, "__args__"):
            return any(self._is_protocol_type(arg) for arg in type_hint.__args__)
        return getattr(type_hint, "_is_protocol", False)

    def _validate_endpoint_uri(self, value: Any, field_name: str) -> None:
        if (
            value is not None
            and not isinstance(value, str)
            and not (hasattr(value, "scheme") and hasattr(value, "host"))
        ):
            raise TypeError(f"{field_name} must be a string or URI")

    async def _resolve_aws_credentials_identity_resolver(
        self,
        constructor_values: dict[str, Any],
        env_values: dict[str, Any],
        config_file_values: dict[str, Any],
        credentials_file_values: dict[str, Any],
        default_value: Any,
        validator: str | None,
    ) -> ConfigValue:
        if "aws_credentials_identity_resolver" in constructor_values:
            return ConfigValue(
                constructor_values["aws_credentials_identity_resolver"],
                SOURCE_CONSTRUCTOR,
            )
        return ConfigValue(default_value, SOURCE_DEFAULT)

    def get_config_value_object(self, field_name: str) -> ConfigValue:
        """Get the raw ConfigValue object for a field"""
        if not self._resolved:
            raise RuntimeError("Config must be resolved before accessing values")
        return getattr(self, f"_{field_name}")

    @property
    def aws_access_key_id(self) -> str | None:
        return self._aws_access_key_id.value

    @aws_access_key_id.setter
    def aws_access_key_id(self, value: str | None) -> None:
        self._aws_access_key_id = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def aws_credentials_identity_resolver(
        self,
    ) -> IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None:
        return self._aws_credentials_identity_resolver.value

    @aws_credentials_identity_resolver.setter
    def aws_credentials_identity_resolver(
        self,
        value: IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None,
    ) -> None:
        self._aws_credentials_identity_resolver = ConfigValue(
            value, SOURCE_IN_CODE_UPDATE
        )

    @property
    def aws_secret_access_key(self) -> str | None:
        return self._aws_secret_access_key.value

    @aws_secret_access_key.setter
    def aws_secret_access_key(self, value: str | None) -> None:
        self._aws_secret_access_key = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def aws_session_token(self) -> str | None:
        return self._aws_session_token.value

    @aws_session_token.setter
    def aws_session_token(self, value: str | None) -> None:
        self._aws_session_token = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def endpoint_resolver(self) -> EndpointResolver | None:
        return self._endpoint_resolver.value

    @endpoint_resolver.setter
    def endpoint_resolver(self, value: EndpointResolver | None) -> None:
        self._endpoint_resolver = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def endpoint_uri(self) -> str | URI | None:
        return self._endpoint_uri.value

    @endpoint_uri.setter
    def endpoint_uri(self, value: str | URI | None) -> None:
        self._endpoint_uri = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def http_request_config(self) -> HTTPRequestConfiguration | None:
        return self._http_request_config.value

    @http_request_config.setter
    def http_request_config(self, value: HTTPRequestConfiguration | None) -> None:
        self._http_request_config = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def region(self) -> str | None:
        return self._region.value

    @region.setter
    def region(self, value: str | None) -> None:
        self._region = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def retry_strategy(self) -> RetryStrategy:
        return self._retry_strategy.value

    @retry_strategy.setter
    def retry_strategy(self, value: RetryStrategy) -> None:
        self._retry_strategy = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def sdk_ua_app_id(self) -> str | None:
        return self._sdk_ua_app_id.value

    @sdk_ua_app_id.setter
    def sdk_ua_app_id(self, value: str | None) -> None:
        self._sdk_ua_app_id = ConfigValue(value, SOURCE_IN_CODE_UPDATE)

    @property
    def user_agent_extra(self) -> str | None:
        return self._user_agent_extra.value

    @user_agent_extra.setter
    def user_agent_extra(self, value: str | None) -> None:
        self._user_agent_extra = ConfigValue(value, SOURCE_IN_CODE_UPDATE)
