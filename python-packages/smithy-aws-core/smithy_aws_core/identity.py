# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from smithy_core.identity import Identity


class AWSCredentialIdentity(Identity):
    """Container for AWS authentication credentials."""

    def __init__(
        self,
        *,
        access_key_id: str,
        secret_access_key: str,
        session_token: str | None = None,
        expiration: datetime | None = None,
    ) -> None:
        """Initialize the AWSCredentialIdentity.

        :param access_key_id: A unique identifier for an AWS user or role.
        :param secret_access_key: A secret key used in conjunction with the access key
            ID to authenticate programmatic access to AWS services.
        :param session_token: A temporary token used to specify the current session for
            the supplied credentials.
        :param expiration: The expiration time of the identity. If time zone is
            provided, it is updated to UTC. The value must always be in UTC.
        """
        super().__init__(expiration=expiration)
        self._access_key_id: str = access_key_id
        self._secret_access_key: str = secret_access_key
        self._session_token: str | None = session_token

    @property
    def access_key_id(self) -> str:
        return self._access_key_id

    @property
    def secret_access_key(self) -> str:
        return self._secret_access_key

    @property
    def session_token(self) -> str | None:
        return self._session_token
