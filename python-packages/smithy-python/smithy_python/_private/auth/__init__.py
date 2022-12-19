# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from typing import Any

from smithy_python.interfaces import http as http_interface
from smithy_python.interfaces import identity as identity_interface


class Identity:
    def __init__(self, expiration: datetime | None = None) -> None:
        self._expiration: datetime | None = expiration

    @property
    def expiration(self) -> datetime | None:
        return self._expiration

    @property
    def expired(self) -> bool:
        if self.expiration is None:
            return False
        return datetime.now() > self.expiration


class HttpSigner:
    def sign(
        self,
        http_request: http_interface.Request,
        identity: identity_interface.Identity,
        signing_properties: dict[str, Any],
    ) -> http_interface.Request:
        raise NotImplementedError()
