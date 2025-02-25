# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import os
import platform
from string import ascii_letters, digits
from typing import NamedTuple, Optional, Self

from smithy_http.aio.crt import HAS_CRT

_USERAGENT_ALLOWED_CHARACTERS = ascii_letters + digits + "!$%&'*+-.^_`|~"
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
_USERAGENT_SDK_NAME = "aws-sdk-python"


class UserAgent:
    def __init__(
        self,
        platform_name,
        platform_version,
        platform_machine,
        python_version,
        python_implementation,
        execution_env,
        crt_version=None,
    ) -> None:
        self._platform_name = platform_name
        self._platform_version = platform_version
        self._platform_machine = platform_machine
        self._python_version = python_version
        self._python_implementation = python_implementation
        self._execution_env = execution_env
        self._crt_version = crt_version

        # Components that can be added with ``set_config``
        self._user_agent_suffix = None
        self._user_agent_app_id = None
        self._sdk_version = None

    @classmethod
    def from_environment(cls) -> Self:
        crt_version = None
        if HAS_CRT:
            crt_version = _get_crt_version() or "Unknown"
        return cls(
            platform_name=platform.system(),
            platform_version=platform.release(),
            platform_machine=platform.machine(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            execution_env=os.environ.get("AWS_EXECUTION_ENV"),
            crt_version=crt_version,
        )

    def with_config(
        self,
        ua_suffix: str | None = None,
        ua_app_id: str | None = None,
        sdk_version: str | None = None,
    ) -> Self:
        self._user_agent_suffix = ua_suffix
        self._user_agent_app_id = ua_app_id
        self._sdk_version = sdk_version
        return self

    def to_string(self):
        """Build User-Agent header string from the object's properties."""
        components = [
            *self._build_sdk_metadata(),
            UserAgentComponent("ua", "2.0"),
            *self._build_os_metadata(),
            *self._build_architecture_metadata(),
            *self._build_language_metadata(),
            *self._build_execution_env_metadata(),
            *self._build_feature_metadata(),
            *self._build_app_id(),
            *self._build_suffix(),
        ]

        return " ".join([comp.to_string() for comp in components])

    def _build_sdk_metadata(self):
        """Build the SDK name and version component of the User-Agent header.

        Includes CRT version if available.
        """
        sdk_md = []
        sdk_md.append(UserAgentComponent(_USERAGENT_SDK_NAME, self._sdk_version))

        if self._crt_version is not None:
            sdk_md.append(UserAgentComponent("md", "awscrt", self._crt_version))

        return sdk_md

    def _build_os_metadata(self):
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
        if self._platform_name is None:
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

    def _build_architecture_metadata(self):
        """Build architecture component of the User-Agent header string.

        Returns the machine type with prefix "md" and name "arch", if one is available.
        Common values include "x86_64", "arm64", "i386".
        """
        if self._platform_machine:
            return [UserAgentComponent("md", "arch", self._platform_machine.lower())]
        return []

    def _build_language_metadata(self):
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

    def _build_execution_env_metadata(self):
        """Build the execution environment component of the User-Agent header.

        Returns a single component prefixed with "exec-env", usually sourced from the
        environment variable AWS_EXECUTION_ENV.
        """
        if self._execution_env:
            return [UserAgentComponent("exec-env", self._execution_env)]
        else:
            return []

    def _build_feature_metadata(self):
        """Build the features components of the User-Agent header string.

        TODO: These should be sourced from property bag set on context.
        """
        return []

    def _build_app_id(self):
        """Build app component of the User-Agent header string."""
        if self._user_agent_app_id:
            return [UserAgentComponent("app", self._user_agent_app_id)]
        else:
            return []

    def _build_suffix(self):
        if self._user_agent_suffix:
            return [RawStringUserAgentComponent(self._user_agent_suffix)]
        else:
            return []


def sanitize_user_agent_string_component(raw_str, allow_hash):
    """Replaces all not allowed characters in the string with a dash ("-").

    Allowed characters are ASCII alphanumerics and ``!$%&'*+-.^_`|~``. If
    ``allow_hash`` is ``True``, "#"``" is also allowed.

    :type raw_str: str
    :param raw_str: The input string to be sanitized.

    :type allow_hash: bool
    :param allow_hash: Whether "#" is considered an allowed character.
    """
    return "".join(
        c if c in _USERAGENT_ALLOWED_CHARACTERS or (allow_hash and c == "#") else "-"
        for c in raw_str
    )


class UserAgentComponent(NamedTuple):
    """Component of a User-Agent header string in the standard format.

    Each component consists of a prefix, a name, and a value. In the string
    representation these are combined in the format ``prefix/name#value``.

    This class is considered private and is subject to abrupt breaking changes.
    """

    prefix: str
    name: str
    value: Optional[str] = None

    def to_string(self):
        """Create string like 'prefix/name#value' from a UserAgentComponent."""
        clean_prefix = sanitize_user_agent_string_component(
            self.prefix, allow_hash=True
        )
        clean_name = sanitize_user_agent_string_component(self.name, allow_hash=False)
        if self.value is None or self.value == "":
            return f"{clean_prefix}/{clean_name}"
        clean_value = sanitize_user_agent_string_component(self.value, allow_hash=True)
        return f"{clean_prefix}/{clean_name}#{clean_value}"


class RawStringUserAgentComponent:
    """UserAgentComponent interface wrapper around ``str``.

    Use for User-Agent header components that are not constructed from prefix+name+value
    but instead are provided as strings. No sanitization is performed.
    """

    def __init__(self, value):
        self._value = value

    def to_string(self):
        return self._value


def _get_crt_version():
    """This function is considered private and is subject to abrupt breaking changes."""
    try:
        import awscrt

        return awscrt.__version__
    except AttributeError:
        return None
