import pytest
from typing import Any, Dict

from smithy_python._private.collection import SmithyEntry
from smithy_python._private.http import Request, URL, Response
from smithy_python._private.middleware import (
    SmithyStack,
    SerializeInput,
    SerializeOutput,
    SerializeHandler,
    FinalizeInput,
    FinalizeOutput,
    FinalizeHandler,
    DeserializeInput,
    DeserializeOutput,
    Handler,
    Middleware,
    InitializeInput,
    BuildInput,
)


@pytest.fixture  # type: ignore
def dummy_request() -> Request:
    return Request(url=URL(hostname="example.com"))


@pytest.fixture  # type: ignore
def dummy_response() -> Response:
    return Response(status_code=200, headers=[], body=None)


def test_default_step_context(dummy_request: Request, dummy_response: Response) -> None:
    initialize_input = InitializeInput[None](param=None)
    assert initialize_input.context == {}

    serialize_input = SerializeInput[None](param=None)
    assert serialize_input.context == {}

    build_input = BuildInput[None](param=None, request=dummy_request)
    assert build_input.context == {}

    finalize_input = FinalizeInput[None](param=None, request=dummy_request)
    assert finalize_input.context == {}

    deserialize_input = DeserializeInput[None](
        param=None, request=dummy_request, response=dummy_response
    )
    assert deserialize_input.context == {}


def serialize_request(
    next_handler: SerializeHandler[Any, str]
) -> SerializeHandler[Any, str]:
    def _serialize(param: SerializeInput[Any]) -> SerializeOutput[str]:
        param.request = Request(url=URL(hostname="example.com"))
        return next_handler(param)

    return _serialize


def stub_response(next_handler: FinalizeHandler[Any, str]) -> FinalizeHandler[Any, str]:
    def _stub_response(param: FinalizeInput[Any]) -> FinalizeOutput[str]:
        param.response = Response(status_code=200, headers=[], body=str(param.input))
        return next_handler(param)

    return _stub_response


def deserialize_response(param: DeserializeInput[Any]) -> DeserializeOutput[str]:
    output: str = param.response.body
    return DeserializeOutput(output=output)


def test_smithy_stack_int_to_str() -> None:
    stack = SmithyStack[int, str]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    handler = stack.resolve(deserialize_response, {})
    result = handler(5)
    assert result == "5"


def test_context_plumbed_through() -> None:
    stack = SmithyStack[None, str]()
    stack.serialize.add_before(SmithyEntry(serialize_request, "serialize_request"))
    stack.finalize.add_after(SmithyEntry(stub_response, "stub_response"))

    def add_param_type(next_handler: Handler[Any, Any]) -> Handler[Any, Any]:
        def _add_type(param: Any) -> Any:
            param.context["steps"].append(type(param))
            return next_handler(param)

        return _add_type

    entry: SmithyEntry[Middleware[Any, Any]] = SmithyEntry(
        add_param_type, "add_param_type"
    )

    stack.initialize.add_before(entry)
    stack.serialize.add_before(entry)
    stack.build.add_before(entry)
    stack.finalize.add_before(entry)
    stack.deserialize.add_before(entry)

    context: Dict[Any, Any] = {"steps": []}
    handler = stack.resolve(deserialize_response, context)
    handler(None)
    expected_steps = [
        InitializeInput,
        SerializeInput,
        BuildInput,
        FinalizeInput,
        DeserializeInput,
    ]
    assert context["steps"] == expected_steps
