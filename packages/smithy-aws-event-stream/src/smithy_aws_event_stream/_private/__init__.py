# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from smithy_core.schemas import Schema
from smithy_core.traits import EventPayloadTrait

INITIAL_REQUEST_EVENT_TYPE = "initial-request"
INITIAL_RESPONSE_EVENT_TYPE = "initial-response"


def get_payload_member(schema: Schema) -> Schema | None:
    for member in schema.members.values():
        if EventPayloadTrait in member:
            return member
    return None
