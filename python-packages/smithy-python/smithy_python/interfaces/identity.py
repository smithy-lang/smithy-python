# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from datetime import datetime
from typing import Protocol, TypeVar


class Identity(Protocol):
    """An entity within the SDK representing who the customer is."""

    expiration: datetime | None = None


IdentityType = TypeVar("IdentityType", bound=Identity)


class TokenIdentity(Identity):

    token: str


class LoginIdentity(Identity):

    username: str
    password: str


class AnonymousIdentity(Identity):
    ...
