# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AWS SDK Signers provides stand-alone signing functionality for use with HTTP tools
such as AioHTTP, Curl, Postman, Requests, urllib3, etc."""

from __future__ import annotations

from ._http import URI, AWSRequest, Field, Fields
from ._identity import AWSCredentialIdentity
from ._io import AsyncBytesReader
from ._version import __version__
from .signers import AsyncSigV4Signer, SigV4Signer, SigV4SigningProperties

__license__ = "Apache-2.0"
__version__ = __version__

__all__ = (
    "AsyncBytesReader",
    "AsyncSigV4Signer",
    "AWSCredentialIdentity",
    "AWSRequest",
    "Field",
    "Fields",
    "SigV4Signer",
    "SigV4SigningProperties",
    "URI",
)
