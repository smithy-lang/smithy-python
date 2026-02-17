#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.traits import (
    AwsJson1_0Trait,
    AwsJson1_1Trait,
    RestJson1Trait,
)


@pytest.mark.parametrize(
    "trait_type",
    [RestJson1Trait, AwsJson1_0Trait, AwsJson1_1Trait],
)
def test_allows_empty_protocol_trait_value(
    trait_type: type[RestJson1Trait] | type[AwsJson1_0Trait] | type[AwsJson1_1Trait],
) -> None:
    trait = trait_type(None)
    assert trait.http == ("http/1.1",)
    assert trait.event_stream_http == ("http/1.1",)
