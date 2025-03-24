# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AWS SDK Signers provides stand-alone signing functionality for use with HTTP tools
such as AioHTTP, Curl, Postman, Requests, urllib3, etc."""

from __future__ import annotations

import importlib.metadata

from ._http import AWSRequest, Field, Fields, URI
from ._identity import AWSCredentialIdentity
from ._io import AsyncBytesReader
from .signers import (
    AsyncEventSigner,
    AsyncSigV4Signer,
    SigV4Signer,
    SigV4SigningProperties,
)

__license__ = "Apache-2.0"
__version__ = importlib.metadata.version("aws-sdk-signers")

__all__ = (
    "URI",
    "AWSCredentialIdentity",
    "AWSRequest",
    "AsyncBytesReader",
    "AsyncEventSigner",
    "AsyncSigV4Signer",
    "Field",
    "Fields",
    "SigV4Signer",
    "SigV4SigningProperties",
)
