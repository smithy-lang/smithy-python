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

from smithy_python._private.identity import Identity


class AWSCredentialIdentity(Identity):
    """Container for AWS authentication credentials."""

    def __init__(
        self,
        access_key_id: str,
        secret_key_id: str,
        session_token: str | None = None,
        expiration: datetime | None = None,
    ) -> None:
        """Initialize the AWSCredentialIdentity.

        :param access_key_id: The access key ID. A unique identifier that AWS uses to
        authenticate a user or application.
        :param secret_key_id: The secret key ID. A secret key that AWS uses
        authenticate programmatic access to AWS services along with the access key ID.
        :param session_token: The session token. Used to provide temporary, programmatic
        access to AWS services. Typically it expires after 1 hour, after which it must
        be regenerated.
        :param expiration: The expiration time of the credentials. If time zone is
        provided, it will be removed. The value must always be in UTC.
        """
        super().__init__(expiration)
        self._access_key_id: str = access_key_id
        self._secret_key_id: str = secret_key_id
        self._session_token: str | None = session_token

    @property
    def access_key_id(self) -> str:
        return self._access_key_id

    @property
    def secret_key_id(self) -> str:
        return self._secret_key_id

    @property
    def session_token(self) -> str | None:
        return self._session_token
