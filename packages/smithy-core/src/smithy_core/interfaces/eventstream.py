# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Protocol


class EventPublisher(Protocol):
    """Sends events to a service.

    Placeholder for the synchronous event publisher; populated alongside the sync
    client implementation.
    """

    # TODO(sync-api): implement alongside the sync client


class EventReceiver(Protocol):
    """Receives events from a service.

    Placeholder for the synchronous event receiver; populated alongside the sync
    client implementation.
    """

    # TODO(sync-api): implement alongside the sync client
