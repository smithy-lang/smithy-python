#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_aws_core.traits import RestJson1Trait


def test_allows_empty_restjson1_value() -> None:
    trait = RestJson1Trait(None)
    assert trait.http == ("http/1.1",)
