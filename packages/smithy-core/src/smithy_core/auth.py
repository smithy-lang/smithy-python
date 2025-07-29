# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .deserializers import DeserializeableShape
from .interfaces import TypedProperties as _TypedProperties
from .schemas import APIOperation
from .serializers import SerializeableShape
from .shapes import ShapeID
from .types import TypedProperties


@dataclass(kw_only=True, frozen=True)
class AuthParams[I: SerializeableShape, O: DeserializeableShape]:
    """Parameters passed to an AuthSchemeResolver's ``resolve_auth_scheme`` method."""

    protocol_id: ShapeID
    """The ID of the protocol being used for the operation invocation."""

    operation: APIOperation[I, O] = field(repr=False)
    """The schema and associated information about the operation being invoked."""

    context: _TypedProperties
    """The context of the operation invocation."""


@dataclass(kw_only=True)
class AuthOption:
    """Auth scheme used for signing and identity resolution."""

    scheme_id: ShapeID
    """The ID of the auth scheme to use."""

    identity_properties: _TypedProperties = field(default_factory=TypedProperties)
    """Paramters to pass to the identity resolver method."""

    signer_properties: _TypedProperties = field(default_factory=TypedProperties)
    """Paramters to pass to the signing method."""


class DefaultAuthResolver:
    """Determines which authentication scheme to use based on modeled auth schemes."""

    def resolve_auth_scheme(
        self, *, auth_parameters: AuthParams[Any, Any]
    ) -> Sequence[AuthOption]:
        """Resolve an ordered list of applicable auth schemes.

        :param auth_parameters: The parameters required for determining which
            authentication schemes to potentially use.
        """
        return [
            AuthOption(scheme_id=id)
            for id in auth_parameters.operation.effective_auth_schemes
        ]


class NoAuthResolver:
    """Auth resolver that always returns no auth scheme options."""

    def resolve_auth_scheme(
        self, *, auth_parameters: AuthParams[Any, Any]
    ) -> Sequence[AuthOption]:
        return []
