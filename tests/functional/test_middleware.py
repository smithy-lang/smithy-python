from dataclasses import dataclass

from smithy_python._private.collection import SmithyEntry
from smithy_python._private.http import URL, Request, Response
from smithy_python._private.middleware import (
    DeserializeInput,
    DeserializeOutput,
    FinalizeHandler,
    FinalizeInput,
    FinalizeOutput,
    SerializeHandler,
    SerializeInput,
    SerializeOutput,
    SmithyStack,
)


@dataclass
class MyInput:
    text: str


@dataclass
class MyOutput:
    length: int


def serialize_request(
    next_handler: SerializeHandler[MyInput, MyOutput]
) -> SerializeHandler[MyInput, MyOutput]:
    def _serialize(param: SerializeInput[MyInput]) -> SerializeOutput[MyOutput]:
        param.request = Request(
            url=URL(hostname="example.com"),
            method="GET",
            headers=[("host", "example.com")],
            body=param.input.text.encode(),
        )
        return next_handler(param)

    return _serialize


def stub_response(
    next_handler: FinalizeHandler[MyInput, MyOutput]
) -> FinalizeHandler[MyInput, MyOutput]:
    def _stub_response(param: FinalizeInput[MyInput]) -> FinalizeOutput[MyOutput]:
        param.response = Response(
            status_code=200,
            headers=[],
            body=str(len(param.request.body)),
        )
        return next_handler(param)

    return _stub_response


def deserialize_response(
    param: DeserializeInput[MyInput],
) -> DeserializeOutput[MyOutput]:
    output = MyOutput(length=int(param.response.body))
    return DeserializeOutput(output=output)


def test_smithy_stack() -> None:
    stack = SmithyStack[MyInput, MyOutput]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    text = "some text"
    my_input = MyInput(text=text)
    handler = stack.resolve(deserialize_response, {})
    result = handler(my_input)
    assert result.length == len(text)
