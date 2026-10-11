#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest
from smithy_aws_core.identity.chain.ordering import StandardProvider

_ENV_DETECTION_VARS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_ROLE_ARN",
    "AWS_CONTAINER_CREDENTIALS_FULL_URI",
    "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
)


@pytest.mark.parametrize(
    "slot, env, expected",
    [
        (StandardProvider.ENVIRONMENT, {"AWS_ACCESS_KEY_ID": "akid"}, True),
        (
            StandardProvider.WEB_IDENTITY_TOKEN_ENV,
            {
                "AWS_WEB_IDENTITY_TOKEN_FILE": "/token",
                "AWS_ROLE_ARN": "arn:aws:iam::123456789012:role/test",
            },
            True,
        ),
        (
            StandardProvider.WEB_IDENTITY_TOKEN_ENV,
            {"AWS_WEB_IDENTITY_TOKEN_FILE": "/token"},
            False,
        ),
        (
            StandardProvider.ECS_CONTAINER,
            {"AWS_CONTAINER_CREDENTIALS_FULL_URI": "https://example.com"},
            True,
        ),
        (
            StandardProvider.ECS_CONTAINER,
            {"AWS_CONTAINER_CREDENTIALS_RELATIVE_URI": "/credentials"},
            True,
        ),
        (StandardProvider.EC2_INSTANCE_METADATA, {}, False),
        (StandardProvider.PROFILE_STATIC_KEYS, {}, False),
    ],
)
def test_is_detected_with_env(
    slot: StandardProvider,
    env: dict[str, str],
    expected: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in _ENV_DETECTION_VARS:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    assert slot.is_detected() is expected


@pytest.mark.parametrize(
    "create_config, create_credentials, expected",
    [
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    ],
)
def test_shared_config_detection(
    create_config: bool,
    create_credentials: bool,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config"
    credentials_path = tmp_path / "credentials"
    if create_config:
        config_path.write_text("[default]\n")
    if create_credentials:
        credentials_path.write_text("[default]\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config_path))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(credentials_path))

    assert StandardProvider.SHARED_CONFIG.is_detected() is expected


# Regression test to catch accidental edits.
@pytest.mark.parametrize(
    "slot, canonical_name, module_suggestion",
    [
        (StandardProvider.ENVIRONMENT, "Environment", None),
        (
            StandardProvider.WEB_IDENTITY_TOKEN_ENV,
            "WebIdentityTokenEnv",
            "aws-credentials-sts",
        ),
        (StandardProvider.SHARED_CONFIG, "SharedConfig", None),
        (
            StandardProvider.PROFILE_ASSUME_ROLE,
            "ProfileAssumeRole",
            "aws-credentials-sts",
        ),
        (StandardProvider.PROFILE_SESSION_KEYS, "ProfileSessionKeys", None),
        (StandardProvider.PROFILE_STATIC_KEYS, "ProfileStaticKeys", None),
        (
            StandardProvider.PROFILE_WEB_IDENTITY,
            "ProfileWebIdentity",
            "aws-credentials-sts",
        ),
        (
            StandardProvider.PROFILE_SSO_SESSION,
            "ProfileSsoSession",
            "aws-credentials-sso",
        ),
        (StandardProvider.PROFILE_LOGIN, "Login", "aws-credentials-login"),
        (
            StandardProvider.PROFILE_CREDENTIAL_PROCESS,
            "ProfileCredentialProcess",
            None,
        ),
        (StandardProvider.ECS_CONTAINER, "EcsContainer", "aws-credentials-http"),
        (
            StandardProvider.EC2_INSTANCE_METADATA,
            "Ec2InstanceMetadata",
            "aws-credentials-imds",
        ),
    ],
)
def test_slot_metadata(
    slot: StandardProvider,
    canonical_name: str,
    module_suggestion: str | None,
) -> None:
    assert slot.canonical_name == canonical_name
    assert slot.module_suggestion == module_suggestion
