# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from datetime import datetime, timedelta, timezone

import pytest

from smithy_python._private.identity import Identity


def get_current_time() -> datetime:
    return datetime(year=2023, month=1, day=1, tzinfo=timezone.utc)


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
                get_current_time=get_current_time,
            ),
            True,
        ),
        (Identity(), False),
        (
            Identity(
                expiration=datetime(year=2023, month=1, day=2, tzinfo=timezone.utc),
                get_current_time=get_current_time,
            ),
            False,
        ),
        (
            Identity(
                expiration=datetime(year=2022, month=12, day=31, tzinfo=timezone.utc),
                get_current_time=get_current_time,
            ),
            True,
        ),
    ],
)
def test_expired(identity: Identity, expected_expired: bool) -> None:
    assert identity.expired is expected_expired
