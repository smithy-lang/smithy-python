#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_aws_core.traits import AwsQueryErrorTrait, AwsQueryTrait, RestJson1Trait


def test_allows_empty_restjson1_value() -> None:
    trait = RestJson1Trait(None)
    assert trait.http == ("http/1.1",)
    assert trait.event_stream_http == ("http/1.1",)


def test_allows_empty_aws_query_trait_value() -> None:
    trait = AwsQueryTrait(None)
    assert trait.document_value is None


def test_parses_aws_query_error_trait() -> None:
    trait = AwsQueryErrorTrait({"code": "InvalidAction", "httpResponseCode": 400})
    assert trait.code == "InvalidAction"
    assert trait.http_response_code == 400
