import pytest
from dataclasses import dataclass

from smithy_python._private.collection import SmithyEntry
from smithy_python._private.http import Request, URL, Response
from smithy_python._private.middleware import (
    AsyncSmithyStack,
    SerializeInput,
    SerializeOutput,
    AsyncSerializeHandler,
    FinalizeInput,
    FinalizeOutput,
    AsyncFinalizeHandler,
    DeserializeInput,
    DeserializeOutput,
)


@dataclass
class MyInput:
    text: str


@dataclass
class MyOutput:
    length: int


def serialize_request(
    next_handler: AsyncSerializeHandler[MyInput, MyOutput]
) -> AsyncSerializeHandler[MyInput, MyOutput]:
    async def _serialize(param: SerializeInput[MyInput]) -> SerializeOutput[MyOutput]:
        param.request = Request(
            url=URL(hostname="example.com"),
            method="GET",
            headers=[("host", "example.com")],
            body=param.input.text.encode(),
        )
        return await next_handler(param)

    return _serialize


def stub_response(
    next_handler: AsyncFinalizeHandler[MyInput, MyOutput]
) -> AsyncFinalizeHandler[MyInput, MyOutput]:
    async def _stub_response(param: FinalizeInput[MyInput]) -> FinalizeOutput[MyOutput]:
        param.response = Response(
            status_code=200, headers=[], body=str(len(param.request.body)),
        )
        return await next_handler(param)

    return _stub_response


async def deserialize_response(
    param: DeserializeInput[MyInput],
) -> DeserializeOutput[MyOutput]:
    output = MyOutput(length=int(param.response.body))
    return DeserializeOutput(output=output)


@pytest.mark.asyncio  # type: ignore
async def test_smithy_stack() -> None:
    stack = AsyncSmithyStack[MyInput, MyOutput]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    text = "some text"
    my_input = MyInput(text=text)
    handler = stack.resolve(deserialize_response, {})
    result = await handler(my_input)
    assert result.length == len(text)
