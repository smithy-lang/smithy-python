# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from smithy_python._private.auth import Identity


class AwsCredentialIdentity(Identity):
    """Container for AWS authentication credentials."""

    def __init__(
        self,
        access_key_id: str,
        secret_key_id: str,
        session_token: str | None = None,
        expiration: datetime | None = None,
    ) -> None:
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
