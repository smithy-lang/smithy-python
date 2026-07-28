#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from collections.abc import Mapping
from typing import Any, assert_type

import pytest
import smithy_aws_core.identity.chain as chain_module
from smithy_aws_core.identity import (
    AWSCredentialsIdentity,
    AWSIdentityProperties,
    IdentityChain,
)
from smithy_aws_core.identity.chain import (
    IdentityChainConfigurationError,
    IdentityChainError,
)
from smithy_aws_core.identity.chain.ordering import (
    After,
    Before,
    OrderingConstraint,
    Standard,
    StandardProvider,
)
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError


class _StubProvider:
    """A minimal ChainIdentityProvider for exercising assembly logic."""

    def __init__(self, name: str, ordering: OrderingConstraint) -> None:
        self.name = name
        self.ordering = ordering

    async def setup(self, identity_type: type[Any], setup: Any) -> None:
        pass


def _credentials(access_key_id: str) -> AWSCredentialsIdentity:
    return AWSCredentialsIdentity(access_key_id=access_key_id, secret_access_key="s")


class _FakeResolver(IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]):
    def __init__(
        self,
        *,
        identity: AWSCredentialsIdentity | None = None,
        error: SmithyIdentityError | None = None,
    ) -> None:
        self.identity = identity
        self.error = error

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        if self.error is not None:
            raise self.error
        assert self.identity is not None
        return self.identity


async def test_returns_first_successful_resolver() -> None:
    miss = _FakeResolver(error=SmithyIdentityError("miss"))
    hit = _FakeResolver(identity=_credentials("hit"))
    chain = IdentityChain((miss, hit))

    result = await chain.get_identity(properties={})

    assert result.access_key_id == "hit"


async def test_non_identity_errors_propagate() -> None:
    class _BrokenResolver(
        IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
    ):
        async def get_identity(
            self, *, properties: Mapping[str, Any]
        ) -> AWSCredentialsIdentity:
            raise RuntimeError("broken")

    chain = IdentityChain((_BrokenResolver(),))

    with pytest.raises(RuntimeError, match="broken"):
        await chain.get_identity(properties={})


async def test_explicit_chain_preserves_resolvers() -> None:
    resolver = _FakeResolver(identity=_credentials("explicit"))
    chain = IdentityChain((resolver,))

    assert chain._resolvers == (resolver,)
    assert chain.identity_type is None
    assert await chain.get_identity(properties={}) is resolver.identity


async def test_create_records_identity_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chain_module, "_discover_chain_identity_providers", tuple)

    chain = await IdentityChain.create(AWSCredentialsIdentity)

    assert chain.identity_type is AWSCredentialsIdentity
    assert_type(chain, IdentityChain[AWSCredentialsIdentity])


def test_discovers_and_constructs_entry_point_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Provider:
        pass

    class _EntryPoint:
        def load(self) -> Any:
            return _Provider

    def _entry_points(*, group: str) -> tuple[_EntryPoint, ...]:
        assert group == "smithy_aws_core.identity.chain_providers"
        return (_EntryPoint(),)

    monkeypatch.setattr(
        "smithy_aws_core.identity.chain.metadata.entry_points", _entry_points
    )

    discovered = chain_module._discover_chain_identity_providers()

    assert len(discovered) == 1
    assert isinstance(discovered[0], _Provider)


def test_sort_orders_standards_by_slot_declaration() -> None:
    static = _StubProvider(
        "static", Standard(slot=StandardProvider.PROFILE_STATIC_KEYS)
    )
    env = _StubProvider("env", Standard(slot=StandardProvider.ENVIRONMENT))
    shared = _StubProvider("shared", Standard(slot=StandardProvider.SHARED_CONFIG))

    ordered = chain_module._sort_by_ordering((static, env, shared))

    assert [p.name for p in ordered] == ["env", "shared", "static"]


def test_sort_places_before_and_after_around_slot() -> None:
    before = _StubProvider("before", Before(slot=StandardProvider.SHARED_CONFIG))
    shared = _StubProvider("shared", Standard(slot=StandardProvider.SHARED_CONFIG))
    after = _StubProvider("after", After(slot=StandardProvider.SHARED_CONFIG))

    ordered = chain_module._sort_by_ordering((after, shared, before))

    assert [p.name for p in ordered] == ["before", "shared", "after"]


def test_sort_resolves_relative_constraints_without_a_claiming_provider() -> None:
    # No provider claims SHARED_CONFIG, but Before/After still resolve to the
    # slot's declaration position relative to the surrounding standard slots.
    env = _StubProvider("env", Standard(slot=StandardProvider.ENVIRONMENT))
    before = _StubProvider("before", Before(slot=StandardProvider.SHARED_CONFIG))
    static = _StubProvider(
        "static", Standard(slot=StandardProvider.PROFILE_STATIC_KEYS)
    )

    ordered = chain_module._sort_by_ordering((static, before, env))

    assert [p.name for p in ordered] == ["env", "before", "static"]


def test_sort_keeps_discovery_order_for_same_constraint() -> None:
    first = _StubProvider("first", Before(slot=StandardProvider.ENVIRONMENT))
    second = _StubProvider("second", Before(slot=StandardProvider.ENVIRONMENT))

    ordered = chain_module._sort_by_ordering((first, second))

    assert [p.name for p in ordered] == ["first", "second"]


def test_validate_rejects_duplicate_names() -> None:
    first = _StubProvider("dup", Standard(slot=StandardProvider.ENVIRONMENT))
    second = _StubProvider("dup", Standard(slot=StandardProvider.SHARED_CONFIG))

    with pytest.raises(
        IdentityChainConfigurationError,
        match="Credential providers _StubProvider and _StubProvider use the "
        "same name: dup",
    ):
        chain_module._validate_providers((first, second))


def test_validate_rejects_duplicate_standard_slots() -> None:
    first = _StubProvider("a", Standard(slot=StandardProvider.ENVIRONMENT))
    second = _StubProvider("b", Standard(slot=StandardProvider.ENVIRONMENT))

    with pytest.raises(
        IdentityChainConfigurationError,
        match="Credential providers _StubProvider and _StubProvider both claim "
        "standard slot: ENVIRONMENT",
    ):
        chain_module._validate_providers((first, second))


def test_sort_rejects_unsupported_ordering_constraint() -> None:
    class _Unsupported:
        slot = StandardProvider.ENVIRONMENT

    provider = _StubProvider("bad", _Unsupported())  # type: ignore[arg-type]

    with pytest.raises(
        IdentityChainConfigurationError,
        match="Provider _StubProvider returned an unsupported ordering constraint",
    ):
        chain_module._sort_by_ordering((provider,))


async def test_all_miss_raises_with_per_provider_failures() -> None:
    first = _FakeResolver(error=SmithyIdentityError("first miss"))
    second = _FakeResolver(error=SmithyIdentityError("second miss"))
    chain = IdentityChain((first, second))

    with pytest.raises(
        IdentityChainError,
        match="Providers attempted: _FakeResolver: first miss; "
        "_FakeResolver: second miss",
    ) as excinfo:
        await chain.get_identity(properties={})

    assert len(excinfo.value.failures) == 2


async def test_empty_chain_reports_no_configured_provider() -> None:
    chain = IdentityChain((), identity_type=AWSCredentialsIdentity)

    with pytest.raises(
        IdentityChainError,
        match="No credential providers were configured to resolve an identity",
    ):
        await chain.get_identity(properties={})


async def test_chained_invalidate() -> None:
    class _InvalidatingResolver(
        IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
    ):
        def __init__(self) -> None:
            self.invalidated = False

        async def get_identity(
            self, *, properties: AWSIdentityProperties
        ) -> AWSCredentialsIdentity:
            return _credentials("cached")

        async def invalidate(self) -> None:
            self.invalidated = True

    first = _InvalidatingResolver()
    second = _InvalidatingResolver()
    chain = IdentityChain((first, second))

    await chain.invalidate()

    assert first.invalidated
    assert second.invalidated
