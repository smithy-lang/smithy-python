#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from smithy_core.aio.client import AsyncClient
from smithy_core.client import Client
from smithy_core.exceptions import ExpectationNotMetError, ResourceLifecycleError
from smithy_core.interceptors import Interceptor
from smithy_core.retries import RetryStrategyOptions


@dataclass
class _Config:
    protocol: Any = field(default_factory=Mock)
    transport: Any = field(default_factory=Mock)
    endpoint_resolver: Any = field(default_factory=Mock)
    auth_scheme_resolver: Any = field(default_factory=Mock)
    auth_schemes: dict[Any, Any] = field(default_factory=dict[Any, Any])
    interceptors: list[Any] = field(default_factory=list[Any])
    retry_strategy: Any = None
    applied: list[str] = field(default_factory=list[str])


def _plugin(name: str) -> Callable[[_Config], None]:
    def plugin(config: _Config) -> None:
        config.applied.append(name)

    return plugin


class _SyncClient(Client[_Config]):
    _client_plugins = (_plugin("client"),)
    fail_post_setup = False

    def _new_config(self) -> _Config:
        return _Config()

    def _post_setup(self, config: _Config) -> None:
        if self.fail_post_setup:
            raise RuntimeError("post setup failed")
        config.applied.append("post_setup")


class _AsyncClient(AsyncClient[_Config]):
    _client_plugins = (_plugin("client"),)
    fail_post_setup = False

    async def _new_config(self) -> _Config:
        return _Config()

    async def _post_setup(self, config: _Config) -> None:
        if self.fail_post_setup:
            raise RuntimeError("post setup failed")
        config.applied.append("post_setup")


def _operation() -> Any:
    return cast(Any, Mock())


def test_setup_applies_plugins_in_order_without_mutating_caller_config() -> None:
    caller_config = _Config()
    client = _SyncClient(caller_config, plugins=[_plugin("user")])

    _, call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.context["config"].applied == ["client", "user", "post_setup"]
    assert caller_config.applied == []


def test_setup_runs_once() -> None:
    client = _SyncClient()
    client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]
    _, call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.context["config"].applied == ["client", "post_setup"]


def test_failed_post_setup_publishes_nothing() -> None:
    client = _SyncClient(_Config())
    client.fail_post_setup = True

    with pytest.raises(RuntimeError, match="post setup failed"):
        client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    client.fail_post_setup = False
    _, call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]
    assert call.context["config"].applied == ["client", "post_setup"]


def test_operation_plugins_are_scoped_to_the_call() -> None:
    client = _SyncClient()

    _, call = client._prepare_call(  # pyright: ignore[reportPrivateUsage]
        Mock(), _operation(), [_plugin("default")], [_plugin("operation")]
    )
    _, next_call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.context["config"].applied[-2:] == ["default", "operation"]
    assert next_call.context["config"].applied == ["client", "post_setup"]


@pytest.mark.parametrize("plugins", [[], [_plugin("default")]])
def test_configured_interceptors_run_as_the_same_instances(
    plugins: list[Callable[[_Config], None]],
) -> None:
    recorder = _Recorder()
    client = _SyncClient(_Config(interceptors=[recorder]))

    for _ in range(2):
        _, call = client._prepare_call(Mock(), _operation(), plugins, None)  # pyright: ignore[reportPrivateUsage]
        call.interceptor.read_before_execution(Mock())

    assert recorder.calls == 2


async def test_async_configured_interceptors_run_as_the_same_instances() -> None:
    recorder = _Recorder()
    client = _AsyncClient(_Config(interceptors=[recorder]))

    for plugins in ([], [_plugin("default")]):
        _, call = await client._prepare_call(Mock(), _operation(), plugins, None)  # pyright: ignore[reportPrivateUsage]
        call.interceptor.read_before_execution(Mock())

    assert recorder.calls == 2


def test_configured_components_are_shared_with_every_call() -> None:
    caller_config = _Config(retry_strategy=RetryStrategyOptions(max_attempts=2))
    client = _SyncClient(caller_config)

    _, call = client._prepare_call(Mock(), _operation(), [_plugin("default")], None)  # pyright: ignore[reportPrivateUsage]

    config = call.context["config"]
    for name in ("protocol", "transport", "endpoint_resolver", "retry_strategy"):
        assert getattr(config, name) is getattr(caller_config, name)


def test_operation_plugin_interceptors_do_not_persist() -> None:
    recorder = _Recorder()
    caller_config = _Config(interceptors=[recorder])
    client = _SyncClient(caller_config)

    _, call = client._prepare_call(  # pyright: ignore[reportPrivateUsage]
        Mock(), _operation(), [_add_interceptor], None
    )
    _, next_call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert len(call.context["config"].interceptors) == 2
    assert next_call.context["config"].interceptors == [recorder]
    assert caller_config.interceptors == [recorder]


async def test_async_operation_plugin_interceptors_do_not_persist() -> None:
    recorder = _Recorder()
    caller_config = _Config(interceptors=[recorder])
    client = _AsyncClient(caller_config, plugins=[_add_interceptor])

    _, call = await client._prepare_call(  # pyright: ignore[reportPrivateUsage]
        Mock(), _operation(), [_add_interceptor], None
    )
    _, next_call = await client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert len(call.context["config"].interceptors) == 3
    assert len(next_call.context["config"].interceptors) == 2
    assert caller_config.interceptors == [recorder]


def test_incomplete_config_is_rejected() -> None:
    client = _SyncClient(_Config(protocol=None))

    with pytest.raises(ExpectationNotMetError):
        client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]


def test_retry_mode_is_read_from_config_when_present() -> None:
    config = _Config()
    config.retry_mode = "standard"  # type: ignore[attr-defined]
    config.max_attempts = 7  # type: ignore[attr-defined]
    client = _SyncClient(config)

    _, call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.retry_strategy.max_attempts == 7


def test_explicit_retry_strategy_wins() -> None:
    client = _SyncClient(_Config(retry_strategy=RetryStrategyOptions(max_attempts=2)))

    _, call = client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.retry_strategy.max_attempts == 2


def test_closed_client_rejects_calls() -> None:
    client = _SyncClient()
    client.close()

    with pytest.raises(ResourceLifecycleError, match="closed"):
        client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]


async def test_async_setup_matches_sync_setup() -> None:
    caller_config = _Config()
    client = _AsyncClient(caller_config, plugins=[_plugin("user")])

    _, call = await client._prepare_call(  # pyright: ignore[reportPrivateUsage]
        Mock(), _operation(), [_plugin("default")], None
    )
    _, next_call = await client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    assert call.context["config"].applied == ["client", "user", "post_setup", "default"]
    assert next_call.context["config"].applied == ["client", "user", "post_setup"]
    assert caller_config.applied == []


async def test_async_failed_post_setup_publishes_nothing() -> None:
    client = _AsyncClient()
    client.fail_post_setup = True

    with pytest.raises(RuntimeError, match="post setup failed"):
        await client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    client.fail_post_setup = False
    _, call = await client._prepare_call(Mock(), _operation(), [], None)  # pyright: ignore[reportPrivateUsage]
    assert call.context["config"].applied == ["client", "post_setup"]


def test_omitted_input_is_built_from_the_operation() -> None:
    operation: Any = Mock()
    client = _SyncClient()

    _, call = client._prepare_call(None, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    operation.input.assert_called_once_with()
    assert cast(Any, call).input is operation.input.return_value


def test_keyword_members_are_converted_to_the_input_model() -> None:
    operation: Any = Mock()
    members = {"name": "value"}
    client = _SyncClient()

    _, call = client._prepare_call(members, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    operation.model_registry.build_input.assert_called_once_with(
        operation.input_schema, members, operation.schema.id.name
    )
    assert cast(Any, call).input is operation.model_registry.build_input.return_value


def test_input_model_instance_is_used_as_given() -> None:
    operation: Any = Mock()
    model = Mock()
    client = _SyncClient()

    _, call = client._prepare_call(model, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    operation.model_registry.build_input.assert_not_called()
    assert cast(Any, call).input is model


def test_invalid_keyword_members_fail_before_client_setup() -> None:
    operation: Any = Mock()
    operation.model_registry.build_input.side_effect = TypeError("invalid input")
    client = _SyncClient()
    client._new_config = Mock(side_effect=AssertionError("setup ran"))  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(TypeError, match="invalid input"):
        client._prepare_call({"name": 1}, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    assert not client._setup_done  # pyright: ignore[reportPrivateUsage]


async def test_async_invalid_keyword_members_fail_before_client_setup() -> None:
    operation: Any = Mock()
    operation.model_registry.build_input.side_effect = TypeError("invalid input")
    client = _AsyncClient()
    client._new_config = AsyncMock(side_effect=AssertionError("setup ran"))  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(TypeError, match="invalid input"):
        await client._prepare_call({"name": 1}, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    assert not client._setup_done  # pyright: ignore[reportPrivateUsage]


async def test_async_keyword_members_are_converted_to_the_input_model() -> None:
    operation: Any = Mock()
    members = {"name": "value"}
    client = _AsyncClient()

    _, call = await client._prepare_call(members, operation, [], None)  # pyright: ignore[reportPrivateUsage]

    operation.model_registry.build_input.assert_called_once_with(
        operation.input_schema, members, operation.schema.id.name
    )
    assert cast(Any, call).input is operation.model_registry.build_input.return_value


def test_invoke_runs_the_prepared_pipeline() -> None:
    client = _SyncClient()
    pipeline: Any = Mock()
    call: Any = Mock()
    client._prepare_call = Mock(return_value=(pipeline, call))  # pyright: ignore[reportPrivateUsage]

    result = client._invoke(None, _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    pipeline.assert_called_once_with(call)
    assert result is pipeline.return_value


async def test_async_invoke_awaits_the_prepared_pipeline() -> None:
    client = _AsyncClient()
    pipeline: Any = AsyncMock()
    call: Any = Mock()
    client._prepare_call = AsyncMock(return_value=(pipeline, call))  # pyright: ignore[reportPrivateUsage]

    result = await client._invoke(None, _operation(), [], None)  # pyright: ignore[reportPrivateUsage]

    pipeline.assert_awaited_once_with(call)
    assert result is pipeline.return_value


class _Recorder(Interceptor[Any, Any, Any, Any]):
    def __init__(self) -> None:
        self.calls = 0

    def read_before_execution(self, context: Any) -> None:
        self.calls += 1


def _add_interceptor(config: _Config) -> None:
    config.interceptors.append(_Recorder())
