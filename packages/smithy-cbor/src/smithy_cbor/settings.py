#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass(slots=True)
class CBORSettings:
    """Configuration for the CBOR codec."""

    default_namespace: str | None = None
    """Default namespace for resolving a document's discriminator. Not yet consumed:
    the codec does not implement document types."""
