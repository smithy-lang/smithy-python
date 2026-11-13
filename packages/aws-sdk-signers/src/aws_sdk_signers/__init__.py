# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AWS SDK Signers provides stand-alone signing functionality for use with HTTP tools
such as AioHTTP, Curl, Postman, Requests, urllib3, etc."""

from __future__ import annotations

from ._http import AWSRequest, Field, Fields, URI
from ._identity import AWSCredentialIdentity
from .signers import (
    SigV4ChunkSigner,
    SigV4EventSigner,
    SigV4Signer,
    SigV4SigningProperties,
)

__license__ = "Apache-2.0"
__version__ = "0.6.0"

__all__ = (
    "URI",
    "AWSCredentialIdentity",
    "AWSRequest",
    "Field",
    "Fields",
    "SigV4ChunkSigner",
    "SigV4EventSigner",
    "SigV4Signer",
    "SigV4SigningProperties",
)
