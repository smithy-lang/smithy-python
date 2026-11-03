#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Business metrics (feature ID) tracking for the User-Agent header.

Features are recorded in the request properties of each call, where they are used.
When the request is sent, their metric values are added to the ``m/`` section of the
User-Agent header.
"""

import logging
from collections.abc import Iterable
from enum import StrEnum, unique

from smithy_core.interfaces import TypedProperties
from smithy_core.types import PropertyKey

__all__ = [
    "FEATURE_IDS",
    "MAX_ENCODED_FEATURE_IDS_BYTES",
    "AwsFeatureId",
    "encode_feature_ids",
    "register_feature_id",
]

logger = logging.getLogger(__name__)


@unique
class AwsFeatureId(StrEnum):
    """Features that can be tracked.

    Each member is named after the feature ID, and its value is the
    feature's metric value, which is what is sent in the User-Agent header. Only
    features this SDK tracks are listed.
    """

    RETRY_MODE_STANDARD = "E"
    RETRY_MODE_ADAPTIVE = "F"
    ENDPOINT_OVERRIDE = "N"


FEATURE_IDS = PropertyKey(key="feature_ids", value_type=dict[AwsFeatureId, None])
"""Features recorded for the current call, in the order they were registered."""


def register_feature_id(properties: TypedProperties, feature_id: AwsFeatureId) -> None:
    """Record that the current call used a feature.

    Registering a feature that is already recorded has no effect. Features must be
    registered in ``read_after_signing`` or earlier. Features registered later in an
    attempt aren't sent with that attempt. Values that aren't ``AwsFeatureId``
    members are ignored, so that tracking never fails a request.

    :param properties: The request properties of the current call.
    :param feature_id: The feature that was used.
    """
    if not isinstance(feature_id, AwsFeatureId):  # pyright: ignore[reportUnnecessaryIsInstance]
        logger.debug("Ignoring unknown feature ID: %r", feature_id)
        return
    features = properties.get(FEATURE_IDS)
    if features is None:
        features = {}
        properties[FEATURE_IDS] = features
    features[feature_id] = None


MAX_ENCODED_FEATURE_IDS_BYTES = 1024
"""The maximum size of the encoded feature ID list."""


def encode_feature_ids(feature_ids: Iterable[AwsFeatureId]) -> str:
    """Encode features as a comma separated list of metric values of at most 1024 bytes.

    Values are kept in the given order. If the list is too long, values are dropped
    from the end so that no value is ever partially included.

    :param feature_ids: The features to encode, without duplicates.
    """
    encoded = ""
    for feature_id in feature_ids:
        candidate = f"{encoded},{feature_id.value}" if encoded else feature_id.value
        if len(candidate.encode("utf-8")) > MAX_ENCODED_FEATURE_IDS_BYTES:
            break
        encoded = candidate
    return encoded
