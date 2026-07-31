#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from dataclasses import dataclass
from enum import Enum

from ...config import shared_config_files_exist


class StandardProvider(Enum):
    """Defines standard AWS credential provider slots in precedence order."""

    ENVIRONMENT = "Environment", None
    WEB_IDENTITY_TOKEN_ENV = "WebIdentityTokenEnv", "aws-credentials-sts"
    SHARED_CONFIG = "SharedConfig", None
    PROFILE_SESSION_KEYS = "ProfileSessionKeys", None
    PROFILE_STATIC_KEYS = "ProfileStaticKeys", None
    PROFILE_ASSUME_ROLE = "ProfileAssumeRole", "aws-credentials-sts"
    PROFILE_WEB_IDENTITY = "ProfileWebIdentity", "aws-credentials-sts"
    PROFILE_SSO_SESSION = "ProfileSsoSession", "aws-credentials-sso"
    PROFILE_LOGIN = "Login", "aws-credentials-login"
    PROFILE_CREDENTIAL_PROCESS = "ProfileCredentialProcess", None
    ECS_CONTAINER = "EcsContainer", "aws-credentials-http"
    EC2_INSTANCE_METADATA = "Ec2InstanceMetadata", "aws-credentials-imds"

    def __init__(
        self,
        canonical_name: str,
        module_suggestion: str | None,
    ) -> None:
        self.canonical_name = canonical_name
        self.module_suggestion = module_suggestion

    def is_detected(self) -> bool:
        """Return whether this slot has a cheap environment detection signal."""
        match self:
            case StandardProvider.ENVIRONMENT:
                return bool(os.getenv("AWS_ACCESS_KEY_ID"))
            case StandardProvider.WEB_IDENTITY_TOKEN_ENV:
                return bool(os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE")) and bool(
                    os.getenv("AWS_ROLE_ARN")
                )
            case StandardProvider.ECS_CONTAINER:
                return bool(os.getenv("AWS_CONTAINER_CREDENTIALS_FULL_URI")) or bool(
                    os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
                )
            case StandardProvider.SHARED_CONFIG:
                return shared_config_files_exist()
            case _:
                return False


@dataclass(frozen=True, kw_only=True)
class Standard:
    """Claims a standard provider slot."""

    slot: StandardProvider


@dataclass(frozen=True, kw_only=True)
class Before:
    """Positions a provider immediately before a standard provider slot."""

    slot: StandardProvider


@dataclass(frozen=True, kw_only=True)
class After:
    """Positions a provider immediately after a standard provider slot."""

    slot: StandardProvider


type OrderingConstraint = Standard | Before | After
"""Positions a provider at, before, or after a standard provider slot."""
