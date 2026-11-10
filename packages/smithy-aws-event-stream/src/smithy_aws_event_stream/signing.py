# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import TYPE_CHECKING

from smithy_core.interfaces.auth import EventSigner

if TYPE_CHECKING:
    from aws_sdk_signers import SigV4SigningProperties
    from aws_sdk_signers.interfaces.identity import (
        AWSCredentialsIdentity,
        AWSIdentityProperties,
    )

__all__ = ["SigningConfig"]


@dataclass
class SigningConfig[R]:
    """What an event publisher needs to sign the events it sends.

    :param R: The identity resolver type, sync or async.
    """

    signer: "EventSigner[AWSCredentialsIdentity, SigV4SigningProperties]"
    signing_properties: "SigV4SigningProperties"
    identity_resolver: R
    identity_properties: "AWSIdentityProperties"
