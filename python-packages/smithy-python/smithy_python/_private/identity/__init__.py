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
from typing import Callable

from ...interfaces import identity as identity_interface
from ...utils import ensure_utc


class Identity(identity_interface.Identity):
    def __init__(
        self,
        expiration: datetime | None = None,
        get_current_time: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        """Initialize an identity.

        :param expiration: The expiration time of the identity. If time zone is
        provided, it is updated to UTC. The value must always be in UTC.
        """
        if expiration is not None:
            expiration = ensure_utc(expiration)
        self.expiration: datetime | None = expiration
        if get_current_time is None:
            get_current_time = datetime.now
        self.get_current_time = get_current_time

    @property
    def expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return ensure_utc(self.get_current_time()) >= self.expiration
