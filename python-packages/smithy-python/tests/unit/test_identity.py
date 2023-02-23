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

from datetime import datetime

import pytest
import pytz
from freezegun import freeze_time

from smithy_python._private.identity import Identity


@pytest.mark.parametrize(
    "timezone",
    [
        None,
        pytz.timezone("US/Eastern"),
        pytz.timezone("US/Pacific"),
        pytz.utc,
        pytz.timezone("Europe/Paris"),
        pytz.timezone("US/Central"),
    ],
)
def test_expiration_timezone(timezone: pytz.BaseTzInfo) -> None:
    expiration = datetime.now(tz=timezone)
    identity = Identity(expiration=expiration)
    assert identity.expiration is not None
    assert identity.expiration.tzinfo is None


@freeze_time("2021-01-01 00:00:01")
@pytest.mark.parametrize(
    "identity, expected_expired",
    [
        (Identity(expiration=datetime(year=2021, month=1, day=1)), True),
        (Identity(), False),
        (Identity(expiration=datetime(year=2021, month=1, day=2)), False),
        (Identity(expiration=datetime(year=2020, month=12, day=31)), True),
    ],
)
def test_expired(identity: Identity, expected_expired: bool) -> None:
    assert identity.expired is expected_expired
