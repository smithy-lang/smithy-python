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

from ...interfaces import identity as identity_interface


class Identity(identity_interface.Identity):
    def __init__(self, expiration: datetime | None = None) -> None:
        """Initialize an identity.

        :param expiration: The expiration time of the identity. If time zone is
        provided, it will be removed. The value must always be in UTC.
        """
        if expiration is not None and expiration.tzinfo is not None:
            expiration = expiration.replace(tzinfo=None)
        self.expiration: datetime | None = expiration

    @property
    def expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return datetime.now() > self.expiration
