import pytest
from typing import Any, Dict

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
    AsyncHandler,
    AsyncMiddleware,
    InitializeInput,
    BuildInput,
)


def serialize_request(
    next_handler: AsyncSerializeHandler[Any, str]
) -> AsyncSerializeHandler[Any, str]:
    async def _serialize(param: SerializeInput[Any]) -> SerializeOutput[str]:
        param.request = Request(url=URL(hostname="example.com"))
        return await next_handler(param)

    return _serialize


def stub_response(
    next_handler: AsyncFinalizeHandler[Any, str]
) -> AsyncFinalizeHandler[Any, str]:
    async def _stub_response(param: FinalizeInput[Any]) -> FinalizeOutput[str]:
        param.response = Response(status_code=200, headers=[], body=str(param.input))
        return await next_handler(param)

    return _stub_response


async def deserialize_response(param: DeserializeInput[Any]) -> DeserializeOutput[str]:
    output: str = param.response.body
    return DeserializeOutput(output=output)


@pytest.mark.asyncio
async def test_smithy_stack_int_to_str() -> None:
    stack = AsyncSmithyStack[int, str]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    handler = stack.resolve(deserialize_response, {})
    result = await handler(5)
    assert result == "5"


@pytest.mark.asyncio
async def test_context_plumbed_through() -> None:
    stack = AsyncSmithyStack[None, str]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    def add_param_type(next_handler: AsyncHandler[Any, Any]) -> AsyncHandler[Any, Any]:
        async def _add_type(param: Any) -> Any:
            param.context["steps"].append(type(param))
            return await next_handler(param)

        return _add_type

    entry: SmithyEntry[AsyncMiddleware[Any, Any]] = SmithyEntry(
        add_param_type, "add_param_type"
    )

    stack.initialize.add_before(entry)
    stack.serialize.add_before(entry)
    stack.build.add_before(entry)
    stack.finalize.add_before(entry)
    stack.deserialize.add_before(entry)

    context: Dict[Any, Any] = {"steps": []}
    handler = stack.resolve(deserialize_response, context)
    await handler(None)
    expected_steps = [
        InitializeInput,
        SerializeInput,
        BuildInput,
        FinalizeInput,
        DeserializeInput,
    ]
    assert context["steps"] == expected_steps
