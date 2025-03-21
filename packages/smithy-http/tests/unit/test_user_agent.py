import pytest
from smithy_http.user_agent import (
    RawStringUserAgentComponent,
    UserAgent,
    UserAgentComponent,
    sanitize_user_agent_string_component,
)


@pytest.mark.parametrize(
    "raw_str, allow_hash, expected_str",
    [
        ("foo", False, "foo"),
        ("foo", True, "foo"),
        ("ExampleFramework (1.2.3)", False, "ExampleFramework--1.2.3-"),
        ("foo#1.2.3", False, "foo-1.2.3"),
        ("foo#1.2.3", True, "foo#1.2.3"),
        ("", False, ""),
        ("", True, ""),
        ("", False, ""),
        ("#", False, "-"),
        ("#", True, "#"),
        (" ", False, "-"),
        ("  ", False, "--"),
        ("@=[]{ }/\\øß©", True, "------------"),
        (
            "Java_HotSpot_(TM)_64-Bit_Server_VM/25.151-b12",
            True,
            "Java_HotSpot_-TM-_64-Bit_Server_VM-25.151-b12",
        ),
    ],
)
def test_sanitize_ua_string_component(
    raw_str: str, allow_hash: bool, expected_str: str
):
    actual_str = sanitize_user_agent_string_component(raw_str, allow_hash)
    assert actual_str == expected_str


# Test cases for UserAgentComponent
def test_user_agent_component_without_value():
    component = UserAgentComponent(prefix="md", name="test")
    assert str(component) == "md/test"


def test_user_agent_component_with_value():
    component = UserAgentComponent(prefix="md", name="test", value="123")
    assert str(component) == "md/test#123"


def test_user_agent_component_with_empty_value():
    component = UserAgentComponent(prefix="md", name="test", value="")
    assert str(component) == "md/test"


def test_user_agent_component_sanitization():
    component = UserAgentComponent(prefix="md@", name="test!", value="123#")
    assert str(component) == "md-/test!#123#"


# Test cases for RawStringUserAgentComponent
def test_raw_string_user_agent_component():
    component = RawStringUserAgentComponent(value="raw/string#123")
    assert str(component) == "raw/string#123"


# Test cases for UserAgent
def test_user_agent_with_multiple_components():
    sdk_component = UserAgentComponent(prefix="sdk", name="python", value="1.0")
    os_component = UserAgentComponent(prefix="os", name="linux", value="5.4")
    raw_component = RawStringUserAgentComponent(value="raw/string#123")

    user_agent = UserAgent(
        sdk_metadata=[sdk_component],
        os_metadata=[os_component],
        additional_metadata=[raw_component],
    )

    expected_output = "sdk/python#1.0 os/linux#5.4 raw/string#123"
    assert str(user_agent) == expected_output


def test_user_agent_with_empty_metadata():
    user_agent = UserAgent()
    assert str(user_agent) == ""


def test_user_agent_with_all_metadata_types():
    sdk_component = UserAgentComponent(prefix="sdk", name="python", value="1.0")
    internal_component = UserAgentComponent(prefix="md", name="internal")
    ua_component = UserAgentComponent(prefix="ua", name="2.0")
    api_component = UserAgentComponent(prefix="api", name="operation", value="1.1")
    os_component = UserAgentComponent(prefix="os", name="linux", value="5.4")
    language_component = UserAgentComponent(prefix="lang", name="python", value="3.12")
    env_component = UserAgentComponent(prefix="exec-env", name="prod")
    config_component = UserAgentComponent(
        prefix="cfg", name="retry-mode", value="standard"
    )
    feat_component = UserAgentComponent(prefix="ft", name="paginator")
    raw_component = RawStringUserAgentComponent(value="raw/string#123")

    user_agent = UserAgent(
        sdk_metadata=[sdk_component],
        internal_metadata=[internal_component],
        ua_metadata=[ua_component],
        api_metadata=[api_component],
        os_metadata=[os_component],
        language_metadata=[language_component],
        env_metadata=[env_component],
        config_metadata=[config_component],
        feat_metadata=[feat_component],
        additional_metadata=[raw_component],
    )

    expected_output = (
        "sdk/python#1.0 md/internal ua/2.0 api/operation#1.1 os/linux#5.4 "
        "lang/python#3.12 exec-env/prod cfg/retry-mode#standard ft/paginator "
        "raw/string#123"
    )
    assert str(user_agent) == expected_output
