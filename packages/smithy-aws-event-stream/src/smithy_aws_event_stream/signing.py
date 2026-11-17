# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Generic

from smithy_core.interfaces.auth import EventSigner
from smithy_core.interfaces.identity import Identity

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


__all__ = ["SigningConfig"]

_I = TypeVar("_I", bound=Identity, infer_variance=True)
_IP = TypeVar("_IP", bound=Mapping[str, Any], infer_variance=True)
_R = TypeVar("_R", infer_variance=True)
_SP = TypeVar("_SP", bound=Mapping[str, Any], infer_variance=True)


@dataclass
class SigningConfig(Generic[_I, _IP, _SP, _R]):
    """What an event publisher needs to sign the events it sends.

    :param I: The identity type the resolver returns and the signer accepts.
    :param IP: The properties passed to the identity resolver.
    :param SP: The properties passed to the signer.
    :param R: The identity resolver type, sync or async.
    """

    signer: EventSigner[_I, _SP]
    signing_properties: _SP
    identity_resolver: _R
    identity_properties: _IP
