# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import platform
from typing import Any
from unittest.mock import Mock

import pytest
import smithy_core
from smithy_core import URI
from smithy_core.interceptors import InputContext, RequestContext
from smithy_core.types import TypedProperties
from smithy_http import Fields, HTTPRequest
from smithy_http.interceptors.user_agent import (
    USER_AGENT,
    UserAgentInterceptor,
    _UserAgentBuilder,  # type: ignore
)
from smithy_http.user_agent import UserAgentComponent


def test_from_environment(monkeypatch):  # type: ignore
    monkeypatch.setattr(platform, "system", lambda: "Linux")  # type: ignore
    monkeypatch.setattr(platform, "release", lambda: "5.4.228-131.415.AMZN2.X86_64")  # type: ignore
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")  # type: ignore
    monkeypatch.setattr(platform, "python_version", lambda: "4.3.2")  # type: ignore
    monkeypatch.setattr(platform, "python_implementation", lambda: "CPython")  # type: ignore
    monkeypatch.setattr(smithy_core, "__version__", "1.2.3")  # type: ignore

    user_agent = str(_UserAgentBuilder.from_environment().build())
    assert "python/1.2.3" in user_agent
    assert "os/linux#5.4.228-131.415.AMZN2.X86_64" in user_agent
    assert "md/arch#x86_64" in user_agent
    assert "lang/python#4.3.2" in user_agent
    assert "md/pyimpl#CPython" in user_agent


defaults = {
    "platform_name": None,
    "platform_version": None,
    "platform_machine": None,
    "python_version": None,
    "python_implementation": None,
    "sdk_version": None,
}


def test_build_adds_sdk_metadata():
    args = {"sdk_version": "1.2.3"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "python/1.2.3" in str(user_agent)


def test_build_adds_ua_metadata():
    user_agent = _UserAgentBuilder(**defaults).build()
    assert "ua/2.1" in str(user_agent)


def test_build_os_defaults_to_other():
    user_agent = _UserAgentBuilder(**defaults).build()
    assert "os/other" in str(user_agent)


def test_build_os_lowercases_platform():
    args = {"platform_name": "LINUX"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "os/linux" in str(user_agent)


def test_build_os_maps_platform_names():
    args = {"platform_name": "darwin"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()

    assert "os/macos" in str(user_agent)


def test_build_os_includes_version():
    args = {"platform_name": "linux", "platform_version": "5.4"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "os/linux#5.4" in str(user_agent)


def test_build_os_other_platform():
    args = {"platform_name": "myos", "platform_version": "0.0.1"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "os/other md/myos#0.0.1" in str(user_agent)


def test_build_arch_adds_md():
    args = {"platform_machine": "x86_64"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "md/arch#x86_64" in str(user_agent)


def test_build_language_version():
    args = {"python_version": "3.12"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "lang/python#3.12" in str(user_agent)


def test_build_language_implementation():
    args = {"python_implementation": "CPython"}
    user_agent = _UserAgentBuilder(**{**defaults, **args}).build()
    assert "md/pyimpl#CPython" in str(user_agent)


def _start_request(interceptor: UserAgentInterceptor) -> TypedProperties:
    properties = TypedProperties()
    interceptor.read_before_execution(
        InputContext(request=Mock(), properties=properties)
    )
    return properties


def _header(interceptor: UserAgentInterceptor, properties: TypedProperties) -> str:
    request = HTTPRequest(
        method="POST", destination=URI(host="example.com"), fields=Fields(), body=b""
    )
    context = RequestContext[Any, HTTPRequest](
        request=Mock(), transport_request=request, properties=properties
    )
    return interceptor.modify_before_signing(context).fields["User-Agent"].as_string()


def test_interceptor_reads_environment_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def system() -> str:
        nonlocal calls
        calls += 1
        return "Linux"

    monkeypatch.setattr(platform, "system", system)
    interceptor = UserAgentInterceptor()

    headers = [_header(interceptor, _start_request(interceptor)) for _ in range(3)]

    assert calls == 1
    assert headers == [str(_UserAgentBuilder.from_environment().build())] * 3


def test_interceptor_gives_each_request_its_own_user_agent() -> None:
    interceptor = UserAgentInterceptor()
    first = _start_request(interceptor)
    first[USER_AGENT].additional_metadata.append(UserAgentComponent("md", "first"))
    first[USER_AGENT].os_metadata.clear()

    second = _start_request(interceptor)

    assert first[USER_AGENT] is not second[USER_AGENT]
    assert "md/first" not in _header(interceptor, second)
    assert second[USER_AGENT].os_metadata


def test_interceptor_keeps_components_added_during_the_request() -> None:
    interceptor = UserAgentInterceptor()
    properties = _start_request(interceptor)
    properties[USER_AGENT].additional_metadata.append(
        UserAgentComponent("md", "my framework", "1.0")
    )

    assert _header(interceptor, properties).endswith(" md/my-framework#1.0")
