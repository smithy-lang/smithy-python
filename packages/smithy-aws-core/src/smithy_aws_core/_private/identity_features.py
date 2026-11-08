#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Feature IDs recorded by identity resolvers, shared by the sync and async ones."""

from collections.abc import Iterable, Mapping
from typing import Any

from ..business_metrics import AwsFeatureId, add_feature_id

FEATURE_IDS_PROPERTY = "_feature_ids"
"""The identity property holding the call's feature record."""


def record_features(
    properties: Mapping[str, Any], feature_ids: Iterable[AwsFeatureId]
) -> None:
    """Add features to the call's feature record, if the properties carry one."""
    features = properties.get(FEATURE_IDS_PROPERTY)
    if features is None:
        return
    for feature_id in feature_ids:
        add_feature_id(features, feature_id)


def without_feature_record(properties: Mapping[str, Any]) -> dict[str, Any]:
    """Copy the properties without the call's feature record."""
    return {k: v for k, v in properties.items() if k != FEATURE_IDS_PROPERTY}
