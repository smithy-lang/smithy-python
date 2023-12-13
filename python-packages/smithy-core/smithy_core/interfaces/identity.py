#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from typing import Protocol, TypedDict, TypeVar


class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    # The expiration time of the identity. If time zone is provided,
    # it is updated to UTC. The value must always be in UTC.
    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        ...


IdentityType = TypeVar("IdentityType", bound=Identity)
IdentityType_contra = TypeVar("IdentityType_contra", bound=Identity, contravariant=True)
IdentityType_cov = TypeVar("IdentityType_cov", bound=Identity, covariant=True)


class IdentityProperties(TypedDict):
    """Properties used to help determine the identity to return."""

    ...


IdentityPropertiesType = TypeVar("IdentityPropertiesType", bound=IdentityProperties)
IdentityPropertiesType_contra = TypeVar(
    "IdentityPropertiesType_contra", bound=IdentityProperties, contravariant=True
)

IdentityConfig_contra = TypeVar("IdentityConfig_contra", contravariant=True)
