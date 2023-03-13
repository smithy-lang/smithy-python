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

from ..interfaces.auth import HTTPSigner as HTTPSignerInterface
from ..interfaces.auth import SigningPropertiesType_contra
from ..interfaces.http import HTTPRequest as HTTPRequestInterface
from ..interfaces.identity import IdentityType_contra
from .http import HTTPRequest


class HTTPSigner(
    HTTPSignerInterface[IdentityType_contra, SigningPropertiesType_contra]
):
    """An interface for generating a signed HTTP request."""

    async def sign(
        self,
        *,
        http_request: HTTPRequestInterface,
        identity: IdentityType_contra,
        signing_properties: SigningPropertiesType_contra,
    ) -> HTTPRequest:
        """Generate a new signed HTTPRequest based on the one provided.

        :param http_request: The HTTP request to sign.

        :param identity: The signing identity.

        :param signing_properties: Additional properties loaded to modify the
        signing process.
        """
        raise NotImplementedError()
