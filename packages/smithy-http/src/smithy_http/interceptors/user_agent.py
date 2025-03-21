#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import platform
from typing import Any, Self

import smithy_core
from smithy_core.interceptors import InputContext, Interceptor, RequestContext
from smithy_core.types import PropertyKey

from smithy_http import Field
from smithy_http.aio.interfaces import HTTPRequest
from smithy_http.user_agent import UserAgent, UserAgentComponent

USER_AGENT = PropertyKey(key="user_agent", value_type=UserAgent)


class UserAgentInterceptor(Interceptor[Any, Any, HTTPRequest, None]):
    """Adds interceptors that initialize UserAgent in the context and add the user-agent
    header."""

    def read_before_execution(self, context: InputContext[Any]) -> None:
        context.properties[USER_AGENT] = _UserAgentBuilder.from_environment().build()

    def modify_before_signing(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        user_agent = context.properties[USER_AGENT]
        request = context.transport_request
        request.fields.set_field(Field(name="User-Agent", values=[str(user_agent)]))
        return context.transport_request


_USERAGENT_ALLOWED_OS_NAMES = (
    "windows",
    "linux",
    "macos",
    "android",
    "ios",
    "watchos",
    "tvos",
    "other",
)
_USERAGENT_PLATFORM_NAME_MAPPINGS = {"darwin": "macos"}
_USERAGENT_SDK_NAME = "python"


class _UserAgentBuilder:
    def __init__(
        self,
        *,
        platform_name: str | None,
        platform_version: str | None,
        platform_machine: str | None,
        python_version: str | None,
        python_implementation: str | None,
        sdk_version: str | None,
    ) -> None:
        self._platform_name = platform_name
        self._platform_version = platform_version
        self._platform_machine = platform_machine
        self._python_version = python_version
        self._python_implementation = python_implementation
        self._sdk_version = sdk_version

    @classmethod
    def from_environment(cls) -> Self:
        return cls(
            platform_name=platform.system(),
            platform_version=platform.release(),
            platform_machine=platform.machine(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            sdk_version=smithy_core.__version__,
        )

    def build(self) -> UserAgent:
        user_agent = UserAgent()
        user_agent.sdk_metadata.extend(self._build_sdk_metadata())
        user_agent.ua_metadata.append(UserAgentComponent(prefix="ua", name="2.1"))
        user_agent.os_metadata.extend(self._build_os_metadata())
        user_agent.os_metadata.extend(self._build_architecture_metadata())
        user_agent.language_metadata.extend(self._build_language_metadata())

        return user_agent

    def _build_sdk_metadata(self) -> list[UserAgentComponent]:
        if self._sdk_version:
            return [
                UserAgentComponent(prefix=_USERAGENT_SDK_NAME, name=self._sdk_version)
            ]
        return []

    def _build_os_metadata(self) -> list[UserAgentComponent]:
        """Build the OS/platform components of the User-Agent header string.

        For recognized platform names that match or map to an entry in the list
        of standardized OS names, a single component with prefix "os" is
        returned. Otherwise, one component "os/other" is returned and a second
        with prefix "md" and the raw platform name.

        String representations of example return values:
         * ``os/macos#10.13.6``
         * ``os/linux``
         * ``os/other``
         * ``os/other md/foobar#1.2.3``
        """
        if self._platform_name in (None, ""):
            return [UserAgentComponent("os", "other")]

        plt_name_lower = self._platform_name.lower()
        if plt_name_lower in _USERAGENT_ALLOWED_OS_NAMES:
            os_family = plt_name_lower
        elif plt_name_lower in _USERAGENT_PLATFORM_NAME_MAPPINGS:
            os_family = _USERAGENT_PLATFORM_NAME_MAPPINGS[plt_name_lower]
        else:
            os_family = None

        if os_family is not None:
            return [UserAgentComponent("os", os_family, self._platform_version)]
        else:
            return [
                UserAgentComponent("os", "other"),
                UserAgentComponent("md", self._platform_name, self._platform_version),
            ]

    def _build_architecture_metadata(self) -> list[UserAgentComponent]:
        """Build architecture component of the User-Agent header string.

        Returns the machine type with prefix "md" and name "arch", if one is available.
        Common values include "x86_64", "arm64", "i386".
        """
        if self._platform_machine:
            return [UserAgentComponent("md", "arch", self._platform_machine.lower())]
        return []

    def _build_language_metadata(self) -> list[UserAgentComponent]:
        """Build the language components of the User-Agent header string.

        Returns the Python version in a component with prefix "lang" and name
        "python". The Python implementation (e.g. CPython, PyPy) is returned as
        separate metadata component with prefix "md" and name "pyimpl".

        String representation of an example return value:
        ``lang/python#3.10.4 md/pyimpl#CPython``
        """
        lang_md = [
            UserAgentComponent("lang", "python", self._python_version),
        ]
        if self._python_implementation:
            lang_md.append(
                UserAgentComponent("md", "pyimpl", self._python_implementation)
            )
        return lang_md
