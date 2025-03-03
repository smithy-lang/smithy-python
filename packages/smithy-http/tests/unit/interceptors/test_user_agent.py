import platform

import smithy_core
from smithy_http.interceptors.user_agent import _UserAgentBuilder  # type: ignore


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


def test_build_adds_sdk_metadata():
    user_agent = _UserAgentBuilder(sdk_version="1.2.3").build()
    assert "python/1.2.3" in str(user_agent)


def test_build_adds_ua_metadata():
    user_agent = _UserAgentBuilder().build()
    assert "ua/2.1" in str(user_agent)


def test_build_os_defaults_to_other():
    user_agent = _UserAgentBuilder().build()
    assert "os/other" in str(user_agent)


def test_build_os_lowercases_platform():
    user_agent = _UserAgentBuilder(platform_name="LINUX").build()
    assert "os/linux" in str(user_agent)


def test_build_os_maps_platform_names():
    user_agent = _UserAgentBuilder(platform_name="darwin").build()
    assert "os/macos" in str(user_agent)


def test_build_os_includes_version():
    user_agent = _UserAgentBuilder(
        platform_name="linux", platform_version="5.4"
    ).build()
    assert "os/linux#5.4" in str(user_agent)


def test_build_os_other_platform():
    user_agent = _UserAgentBuilder(
        platform_name="myos", platform_version="0.0.1"
    ).build()
    assert "os/other md/myos#0.0.1" in str(user_agent)


def test_build_arch_adds_md():
    user_agent = _UserAgentBuilder(platform_machine="x86_64").build()
    assert "md/arch#x86_64" in str(user_agent)


def test_build_language_version():
    user_agent = _UserAgentBuilder(python_version="3.12").build()
    assert "lang/python#3.12" in str(user_agent)


def test_build_language_implementation():
    user_agent = _UserAgentBuilder(python_implementation="CPython").build()
    assert "md/pyimpl#CPython" in str(user_agent)
