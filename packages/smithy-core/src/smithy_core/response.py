#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ResponseMetadata:
    """Metadata about the transport response that produced a result.

    This is attached to operation outputs and to errors so that callers can
    recover the identifiers a service's support team needs in order to
    investigate a request.

    Every member is optional, since the information available depends on the
    protocol in use and on how far a call progressed before completing. In
    particular, an ``http_status_code`` of ``None`` means that no response was
    received at all, such as when a request timed out or an endpoint could not
    be resolved.
    """

    request_id: str | None = None
    """The service-assigned identifier for the request.

    This is the identifier that AWS support teams ask for when investigating a
    case.
    """

    extended_request_id: str | None = None
    """A secondary identifier for the request, used for debugging.

    Only some services return this. For AWS services it corresponds to the
    ``x-amz-id-2`` header.
    """

    http_status_code: int | None = None
    """The status code of the response.

    A value of ``None`` indicates that no response was received.
    """


EMPTY_RESPONSE_METADATA = ResponseMetadata()
"""Metadata used when no response information is available.

Since :py:class:`ResponseMetadata` is immutable, this is shared rather than
allocated at each use.
"""
