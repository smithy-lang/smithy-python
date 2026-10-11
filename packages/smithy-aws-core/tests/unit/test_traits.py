#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.traits import (
    AwsJson1_0Trait,
    AwsJson1_1Trait,
    AwsQueryErrorTrait,
    AwsQueryTrait,
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


def test_allows_empty_aws_query_trait_value() -> None:
    trait = AwsQueryTrait(None)
    assert trait.document_value is None


def test_parses_aws_query_error_trait() -> None:
    trait = AwsQueryErrorTrait({"code": "InvalidAction", "httpResponseCode": 400})
    assert trait.code == "InvalidAction"
    assert trait.http_response_code == 400
