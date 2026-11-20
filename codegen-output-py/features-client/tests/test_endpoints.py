from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Concatenate

from features_client.aio.client import AsyncFieldNotesClient
from features_client.aio.config import AsyncFieldNotesConfig
from pytest import mark, param
from smithy_core.aio.utils import close_async
from smithy_core.endpoints import BddEndpointResolver
from smithy_core.interceptors import Interceptor
from smithy_core.retries import SimpleRetryStrategy
from smithy_test import check_rules_case
from smithy_test.aio import check_client_case_async

# Endpoint tests from the endpointTests trait of example.features#FieldNotes.

pytestmark = mark.asyncio


_TEST_CONFIG: dict[str, Any] = {
    "region": "us-east-1",
    "aws_access_key_id": "AKIDTEST",
    "aws_secret_access_key": "secret",
}
"Config fields every test sets. A case's own fields replace them."


async def _config(**fields: Any) -> AsyncFieldNotesConfig:
    return await AsyncFieldNotesConfig.resolve(
        **(_TEST_CONFIG | fields), retry_strategy=SimpleRetryStrategy(max_attempts=1)
    )


# Every rules test shares one resolver, so its caches see changing parameters.
_resolver: BddEndpointResolver | None = None


async def _endpoint_resolver() -> BddEndpointResolver:
    global _resolver
    if _resolver is None:
        config = await _config()
        # Only the resolver is used, so the transport is closed right away.
        await close_async(config.transport)
        # The rules checks are sync, so they need the default sync resolver.
        resolver = config.endpoint_resolver
        if not isinstance(resolver, BddEndpointResolver):
            raise TypeError(
                "The default endpoint resolver is not a BddEndpointResolver"
            )
        _resolver = resolver
    return _resolver


async def _client(
    config: Mapping[str, Any], capture: Interceptor[Any, Any, Any, Any]
) -> AsyncFieldNotesClient:
    return AsyncFieldNotesClient(config=await _config(**config, interceptors=[capture]))


RULES_CASES = [
    param(
        {"Stage": "beta", "Kind": "ping"},
        {
            "endpoint": {
                "url": "https://beta.example.com",
                "properties": {"kind": "ping"},
            }
        },
        id="Stage from config",
    ),
    param(
        {"Stage": "beta", "Name": "thing", "Kind": "put"},
        {
            "endpoint": {
                "url": "https://thing.beta.example.com",
                "headers": {"x-kind": ["put"]},
            }
        },
        id="Name from input",
    ),
    param(
        {"Stage": "beta", "Name": "not a label", "Kind": "put"},
        {
            "endpoint": {
                "url": "https://beta.example.com",
                "properties": {"kind": "put"},
            }
        },
        id="Invalid name falls back to the stage",
    ),
    param(
        {"ForcePathStyle": True},
        {"endpoint": {"url": "https://path.example.com"}},
        id="Path style from config",
    ),
    param(
        {"Endpoint": "https://custom.example.com", "Stage": "beta"},
        {"endpoint": {"url": "https://custom.example.com"}},
        id="Custom endpoint",
    ),
    param(
        {"Region": "us-west-2"},
        {"endpoint": {"url": "https://us-west-2.example.com"}},
        id="Region from the built-in",
    ),
    param(
        {},
        {"error": "No stage"},
        id="Missing stage",
    ),
    param(
        {"Kind": "put"},
        {"error": "No stage"},
        id="Missing stage (2)",
    ),
]


@mark.parametrize(("params", "expect"), RULES_CASES)
async def test_endpoint_rules(params: dict[str, Any], expect: dict[str, Any]) -> None:
    check_rules_case(await _endpoint_resolver(), params, expect)


CLIENT_CASES = [
    param(
        {"stage": "beta"},
        AsyncFieldNotesClient.ping,
        {},
        {
            "endpoint": {
                "url": "https://beta.example.com",
                "properties": {"kind": "ping"},
            }
        },
        id="Stage from config",
    ),
    param(
        {"stage": "beta"},
        AsyncFieldNotesClient.put_thing,
        {"name": "thing", "tag": {"key": "k", "value": "v"}, "plugins_": ["p"]},
        {
            "endpoint": {
                "url": "https://thing.beta.example.com",
                "headers": {"x-kind": ["put"]},
            }
        },
        id="Name from input",
    ),
    param(
        {"stage": "beta"},
        AsyncFieldNotesClient.put_thing,
        {"name": "not a label"},
        {
            "endpoint": {
                "url": "https://beta.example.com",
                "properties": {"kind": "put"},
            }
        },
        id="Invalid name falls back to the stage",
    ),
    param(
        {"force_path_style": True},
        AsyncFieldNotesClient.ping,
        {},
        {"endpoint": {"url": "https://path.example.com"}},
        id="Path style from config",
    ),
    param(
        {"endpoint_uri": "https://custom.example.com", "stage": "beta"},
        AsyncFieldNotesClient.ping,
        {},
        {"endpoint": {"url": "https://custom.example.com"}},
        id="Custom endpoint",
    ),
    param(
        {},
        AsyncFieldNotesClient.ping,
        {},
        {"endpoint": {"url": "https://us-west-2.example.com"}},
        id="Region from the built-in",
        marks=mark.skip(reason="No config field sets the built-in AWS::Region"),
    ),
    param(
        {},
        AsyncFieldNotesClient.ping,
        {},
        {"error": "No stage"},
        id="Missing stage",
    ),
]


@mark.parametrize(("config", "operation", "input", "expect"), CLIENT_CASES)
async def test_endpoint_client(
    config: dict[str, Any],
    operation: Callable[Concatenate[AsyncFieldNotesClient, ...], Awaitable[Any]],
    input: dict[str, Any],
    expect: dict[str, Any],
) -> None:
    await check_client_case_async(
        lambda capture: _client(config, capture), operation, input, expect
    )
