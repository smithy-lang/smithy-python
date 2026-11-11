# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smithy_core.interfaces.auth import EventSigner
from smithy_core.interfaces.identity import Identity

__all__ = ["SigningConfig"]


@dataclass
class SigningConfig[
    I: Identity,
    IP: Mapping[str, Any],
    SP: Mapping[str, Any],
    R,
]:
    """What an event publisher needs to sign the events it sends.

    :param I: The identity type the resolver returns and the signer accepts.
    :param IP: The properties passed to the identity resolver.
    :param SP: The properties passed to the signer.
    :param R: The identity resolver type, sync or async.
    """

    signer: EventSigner[I, SP]
    signing_properties: SP
    identity_resolver: R
    identity_properties: IP
