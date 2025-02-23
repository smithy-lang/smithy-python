#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from smithy_core.identity import Identity


@pytest.mark.parametrize(
    "time_zone",
    [
        None,
        timezone(timedelta(hours=3)),
        timezone(timedelta(hours=-3)),
        timezone.utc,
        timezone(timedelta(hours=0)),
        timezone(timedelta(hours=0, minutes=30)),
        timezone(timedelta(hours=0, minutes=-30)),
    ],
)
def test_expiration_timezone(time_zone: timezone) -> None:
    expiration = datetime.now(tz=time_zone)
    identity = Identity(expiration=expiration)
    assert identity.expiration is not None
    assert identity.expiration.tzinfo == timezone.utc


@pytest.mark.parametrize(
    "identity, expected_expired",
    [
        (
            Identity(
                expiration=datetime(year=2023, month=1, day=1, tzinfo=timezone.utc),
            ),
            True,
        ),
        (Identity(), False),
        (
            Identity(
                expiration=datetime(year=2023, month=1, day=2, tzinfo=timezone.utc),
            ),
            False,
        ),
        (
            Identity(
                expiration=datetime(year=2022, month=12, day=31, tzinfo=timezone.utc),
            ),
            True,
        ),
    ],
)
@freeze_time("2023-01-01")
def test_is_expired(identity: Identity, expected_expired: bool) -> None:
    assert identity.is_expired is expected_expired
