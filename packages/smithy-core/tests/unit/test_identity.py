#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from freezegun import freeze_time
from smithy_core.identity import CachingIdentityResolver
from smithy_core.interfaces.identity import Identity


@dataclass(kw_only=True)
class EmptyIdentity(Identity):
    expiration: datetime | None = None


@pytest.mark.parametrize(
    "time_zone",
    [
        None,
        timezone(timedelta(hours=3)),
        timezone(timedelta(hours=-3)),
        UTC,
        timezone(timedelta(hours=0)),
        timezone(timedelta(hours=0, minutes=30)),
        timezone(timedelta(hours=0, minutes=-30)),
    ],
)
def test_expiration_timezone(time_zone: timezone) -> None:
    expiration = datetime.now(tz=time_zone)
    identity = EmptyIdentity(expiration=expiration)
    assert identity.expiration is not None
    assert identity.expiration.tzinfo == UTC


@pytest.mark.parametrize(
    "identity, expected_expired",
    [
        (
            EmptyIdentity(
                expiration=datetime(year=2023, month=1, day=1, tzinfo=UTC),
            ),
            True,
        ),
        (EmptyIdentity(), False),
        (
            EmptyIdentity(
                expiration=datetime(year=2023, month=1, day=2, tzinfo=UTC),
            ),
            False,
        ),
        (
            EmptyIdentity(
                expiration=datetime(year=2022, month=12, day=31, tzinfo=UTC),
            ),
            True,
        ),
    ],
)
@freeze_time("2023-01-01")
def test_is_expired(identity: Identity, expected_expired: bool) -> None:
    assert identity.is_expired is expected_expired


class _CountingResolver(CachingIdentityResolver[EmptyIdentity, dict[str, Any]]):
    def __init__(self) -> None:
        super().__init__()
        self.fetches = 0
        self.started = threading.Event()
        self.release = threading.Event()

    def _get_identity(self, *, properties: dict[str, Any]) -> EmptyIdentity:
        self.fetches += 1
        self.started.set()
        self.release.wait(timeout=5)
        return EmptyIdentity()


def test_concurrent_callers_share_one_fetch() -> None:
    resolver = _CountingResolver()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(resolver.get_identity, properties={}) for _ in range(8)]
        assert resolver.started.wait(timeout=5)
        resolver.release.set()
        identities = {id(f.result()) for f in futures}

    assert resolver.fetches == 1
    assert len(identities) == 1


class _StaticResolver(CachingIdentityResolver[EmptyIdentity, dict[str, Any]]):
    def __init__(self) -> None:
        super().__init__()
        self.fetches = 0

    def _get_identity(self, *, properties: dict[str, Any]) -> EmptyIdentity:
        self.fetches += 1
        return EmptyIdentity()


def test_deepcopy_keeps_the_cache_with_a_new_lock() -> None:
    resolver = _StaticResolver()
    identity = resolver.get_identity(properties={})

    copied = deepcopy(resolver)

    assert copied._lock is not resolver._lock  # pyright: ignore[reportPrivateUsage]
    assert copied.get_identity(properties={}) == identity
    assert copied.fetches == 1
