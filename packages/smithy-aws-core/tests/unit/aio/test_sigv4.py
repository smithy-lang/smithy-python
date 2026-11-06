#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_aws_core.aio.auth.sigv4 import AsyncSigV4AuthScheme
from smithy_aws_core.business_metrics import (
    FEATURE_IDS,
    AwsFeatureId,
    add_feature_id,
    register_feature_id,
)
from smithy_core.types import TypedProperties


@dataclass
class _Config:
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None


def _identity_properties(context: TypedProperties) -> dict[str, object]:
    scheme = AsyncSigV4AuthScheme(service="svc")
    return dict(scheme.identity_properties(context=context))


def test_identity_properties_share_the_call_feature_record() -> None:
    context = TypedProperties({"config": _Config()})

    features = _identity_properties(context)["feature_ids"]
    add_feature_id(features, AwsFeatureId.CREDENTIALS_ENV_VARS)  # type: ignore[arg-type]

    # Resolvers add to the same dict the call sends in the User-Agent header.
    assert features is context[FEATURE_IDS]
    assert list(context[FEATURE_IDS]) == [AwsFeatureId.CREDENTIALS_ENV_VARS]


def test_identity_properties_keep_features_already_recorded() -> None:
    context = TypedProperties({"config": _Config()})
    register_feature_id(context, AwsFeatureId.RETRY_MODE_STANDARD)

    features = _identity_properties(context)["feature_ids"]

    assert features is context[FEATURE_IDS]
    assert list(context[FEATURE_IDS]) == [AwsFeatureId.RETRY_MODE_STANDARD]
