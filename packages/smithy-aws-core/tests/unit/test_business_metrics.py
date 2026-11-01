# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, cast

import pytest
from smithy_aws_core import business_metrics
from smithy_aws_core.business_metrics import (
    FEATURE_IDS,
    MAX_ENCODED_FEATURE_IDS_BYTES,
    AwsFeatureId,
    encode_feature_ids,
    register_feature_id,
)
from smithy_core.types import TypedProperties


def test_register_feature_id_keeps_order_without_duplicates() -> None:
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.RETRY_MODE_STANDARD)
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    register_feature_id(properties, AwsFeatureId.RETRY_MODE_STANDARD)
    assert list(properties[FEATURE_IDS]) == [
        AwsFeatureId.RETRY_MODE_STANDARD,
        AwsFeatureId.ENDPOINT_OVERRIDE,
    ]


def test_encode_feature_ids_uses_metric_values() -> None:
    encoded = encode_feature_ids(
        [AwsFeatureId.RETRY_MODE_STANDARD, AwsFeatureId.ENDPOINT_OVERRIDE]
    )
    assert encoded == "E,N"


def test_encode_feature_ids_empty() -> None:
    assert encode_feature_ids([]) == ""


def test_encode_feature_ids_drops_whole_values_past_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A 4-byte limit fits "E,F" but not "E,F,N", so N is dropped whole.
    monkeypatch.setattr(business_metrics, "MAX_ENCODED_FEATURE_IDS_BYTES", 4)
    encoded = encode_feature_ids(
        [
            AwsFeatureId.RETRY_MODE_STANDARD,
            AwsFeatureId.RETRY_MODE_ADAPTIVE,
            AwsFeatureId.ENDPOINT_OVERRIDE,
        ]
    )
    assert encoded == "E,F"


def test_max_encoded_feature_ids_bytes_is_1024() -> None:
    assert MAX_ENCODED_FEATURE_IDS_BYTES == 1024


def test_register_feature_id_ignores_plain_strings() -> None:
    properties = TypedProperties()
    register_feature_id(properties, cast(Any, "N"))
    assert FEATURE_IDS not in properties
