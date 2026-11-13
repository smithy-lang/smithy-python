# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Consumer imports checked against the native stubs, including partition facades."""

from typing import Literal, assert_type

from awsjson10.models import FooEnum as Json10Enum
from awsjson11.models import FooEnum as Json11Enum
from awsquery.models import GreetingStruct as QueryGreeting
from ec2query.models import GreetingStruct as EC2Greeting
from example_types.models import (
    Code,
    ExampleValue,
    ExampleValueEmpty,
    GetExampleOutput,
    RenamedExample,
    Status,
    Unit,
)
from my_handwritten_json_model.models import Alpha as JSONEvent
from my_handwritten_model.models import (
    Alpha,
    Gamma,
    GammaPayload,
    TradeEvents,
    TradeEventsAlpha,
    TradeEventsBeta,
)
from my_handwritten_model.models import (
    Unit as EventUnit,
)
from nonquerycompatiblerpcv2cbor.models import ServiceError as EmptyServiceError
from partitioned_types.models import (
    PartitionItem000,
    PartitionItem001,
    PartitionItem258,
    PartitionItem259,
)
from querycompatibleawsjson10.models import CustomCodeError as JsonCodeError
from querycompatiblerpcv2cbor.models import CustomCodeError as CBORCodeError
from restjson.models import GreetingStruct as RestJsonGreeting
from restxml.models import GreetingStruct as RestXMLGreeting
from restxmlwithnamespace.models import NestedWithNamespace
from rpcv2cbor.models import (
    RecursiveShapesInputOutputNested1,
    RecursiveShapesInputOutputNested2,
    RpcV2CborListInputOutput,
)
from rpcv2json.models import RpcV2JsonListInputOutput

example = RenamedExample(name="value", status=Status.ACTIVE, code=Code.OK)
choice: ExampleValue = ExampleValueEmpty(value=Unit())
output = GetExampleOutput(example=example, value=choice)
assert_type(example.name, str)
assert_type(output.example, RenamedExample | None)

chain = PartitionItem000(next=PartitionItem001(value="next"))
assert_type(chain.next, PartitionItem001 | None)
assert_type(PartitionItem259().next, PartitionItem258 | None)

events: TradeEvents = TradeEventsAlpha(value=Alpha(id="event"))
unit_event: TradeEvents = TradeEventsBeta(value=EventUnit())
assert_type(Gamma(payload=GammaPayload(values=[1, 2])).payload, GammaPayload | None)

recursive = RecursiveShapesInputOutputNested1(
    nested=RecursiveShapesInputOutputNested2(bar="nested")
)
assert_type(recursive.nested, RecursiveShapesInputOutputNested2 | None)
RpcV2CborListInputOutput(integer_list=[1, 2], nested_string_list=[["value"]])
RpcV2JsonListInputOutput(integer_list=[1, 2], nested_string_list=[["value"]])
assert_type(JSONEvent(id="event").id, str | None)

assert_type(Json10Enum("future").value, Literal["Foo", "Baz", "Bar", "1", "0"])
assert_type(Json11Enum("future").value, Literal["Foo", "Baz", "Bar", "1", "0"])
QueryGreeting(hi="query")
EC2Greeting(hi="ec2")
RestJsonGreeting(hi="json")
RestXMLGreeting(hi="xml")
NestedWithNamespace()
assert_type(JsonCodeError("error").message, str)
assert_type(CBORCodeError("error").message, str)
assert_type(EmptyServiceError("error").message, str)
