# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from ..context import GenerationContext
from ..exceptions import CodegenError
from ..model import JSONValue, Shape, ShapeID, ShapeType
from ..symbols import snake_case
from ..writer import PythonWriter

_REQUEST_TESTS = "smithy.test#httpRequestTests"
_RESPONSE_TESTS = "smithy.test#httpResponseTests"


class ProtocolTestGenerator:
    """Generates executable client HTTP protocol compliance tests."""

    def __init__(self, context: GenerationContext, protocol_id: ShapeID) -> None:
        self.context = context
        self.protocol_id = protocol_id

    def run(self) -> None:
        request_cases: list[tuple[Shape, dict[str, JSONValue]]] = []
        response_cases: list[tuple[Shape, Shape, dict[str, JSONValue]]] = []
        generated = {shape.id for shape in self.context.shapes}
        for operation in self.context.shapes:
            if operation.type is not ShapeType.OPERATION:
                continue
            request_cases.extend(
                (operation, case)
                for case in self._matching(operation.trait(_REQUEST_TESTS, []))
            )
            output = self._target(operation, "output")
            if output is not None:
                response_cases.extend(
                    (operation, self._response_target(case, output), case)
                    for case in self._matching(operation.trait(_RESPONSE_TESTS, []))
                )
            for error_id in self._references(operation, "errors"):
                if error_id not in generated:
                    continue
                error = self.context.model.expect(error_id)
                response_cases.extend(
                    (operation, error, case)
                    for case in self._matching(error.trait(_RESPONSE_TESTS, []))
                )
        if not request_cases and not response_cases:
            return

        writer = PythonWriter()
        self._imports(
            writer, requests=bool(request_cases), responses=bool(response_cases)
        )
        for index, (operation, case) in enumerate(request_cases):
            writer.write(self._request_test(operation, case, index))
            writer.write()
        for index, (operation, target, case) in enumerate(response_cases):
            writer.write(self._response_test(operation, target, case, index))
            writer.write()
        self.context.write(
            "tests/test_protocol.py",
            writer.render(),
            section="protocol.tests",
        )

    def _imports(
        self, writer: PythonWriter, *, requests: bool, responses: bool
    ) -> None:
        module = self.context.settings.module_name
        writer.import_("datetime", "datetime", category="stdlib")
        writer.import_("datetime", "timezone", category="stdlib")
        writer.import_("decimal", "Decimal", category="stdlib")
        writer.import_("json", category="stdlib")
        writer.import_("urllib.parse", "parse_qsl", category="stdlib")
        writer.import_("pytest", category="third_party")
        writer.import_("smithy_core", "URI", category="third_party")
        writer.import_("smithy_core.documents", "Document", category="third_party")
        writer.import_("smithy_core.types", "TypedProperties", category="third_party")
        writer.import_(module, "models", category="local")
        writer.import_(f"{module}.config", "Config", category="local")
        if requests:
            writer.import_(
                "smithy_core.aio.utils",
                "read_streaming_blob_async",
                category="third_party",
            )
            writer.import_("smithy_core.endpoints", "Endpoint", category="third_party")
        if responses:
            writer.import_("smithy_http", "tuples_to_fields", category="third_party")
            writer.import_("smithy_http.aio", "HTTPResponse", category="third_party")
            writer.import_(
                "smithy_http.testing", "create_test_request", category="third_party"
            )

    def _request_test(
        self, operation: Shape, case: Mapping[str, JSONValue], index: int
    ) -> str:
        input_shape = self._target(operation, "input")
        if input_shape is None:
            raise CodegenError(f"Protocol test operation has no input: {operation.id}")
        operation_name = self.context.symbol_provider.to_symbol(operation).name
        test_name = self._test_name(case, "request", operation, index)
        host_value = self._string(case.get("host"), "example.com")
        host, separator, host_path = host_value.partition("/")
        endpoint_path = f"/{host_path}" if separator else None
        resolved_host = self._string(case.get("resolvedHost"), host).split("/", 1)[0]
        params = case.get("params", {})
        input_expression = self._value(input_shape, params)
        method = self._string(case.get("method"), "GET")
        uri = self._string(case.get("uri"), "/")
        query_params = self._string_list(case.get("queryParams"))
        forbid_query = [
            value.lower() for value in self._string_list(case.get("forbidQueryParams"))
        ]
        require_query = [
            value.lower() for value in self._string_list(case.get("requireQueryParams"))
        ]
        headers = self._string_map(case.get("headers"))
        forbid_headers = [
            value.lower() for value in self._string_list(case.get("forbidHeaders"))
        ]
        require_headers = [
            value.lower() for value in self._string_list(case.get("requireHeaders"))
        ]
        endpoint = f"URI(host={host!r}, path={endpoint_path!r})"
        lines = [
            "@pytest.mark.asyncio",
            f"async def test_{test_name}() -> None:",
            "    config = Config()",
            "    protocol = config.protocol",
            "    assert protocol is not None",
            "    request = protocol.serialize_request(",
            f"        operation=models.{operation_name},",
            f"        input={input_expression},",
            f"        endpoint={endpoint},",
            "        context=TypedProperties(),",
            "    )",
            "    request = protocol.set_service_endpoint(",
            "        request=request,",
            f"        endpoint=Endpoint(uri={endpoint}),",
            "    )",
            f"    assert request.method == {method!r}",
            f"    assert request.destination.path == {uri!r}",
            f"    assert request.destination.host == {resolved_host!r}",
            "    actual_query = request.destination.query or ''",
            "    actual_query_segments = actual_query.split('&') if actual_query else []",
            f"    for expected_segment in {query_params!r}:",
            "        assert expected_segment in actual_query_segments",
            "        actual_query_segments.remove(expected_segment)",
            "    actual_query_keys = [",
            "        key.lower()",
            "        for key, _ in parse_qsl(actual_query, keep_blank_values=True)",
            "    ]",
            f"    for forbidden_key in {forbid_query!r}:",
            "        assert forbidden_key not in actual_query_keys",
            f"    for required_key in {require_query!r}:",
            "        assert required_key in actual_query_keys",
            "        actual_query_keys.remove(required_key)",
            f"    expected_headers = {headers!r}",
            "    for expected_name, expected_value in expected_headers.items():",
            "        assert expected_value in request.fields[expected_name].values",
            f"    for forbidden_name in {forbid_headers!r}:",
            "        assert forbidden_name not in request.fields",
            f"    for required_name in {require_headers!r}:",
            "        assert required_name in request.fields",
        ]
        if "body" in case:
            body = self._string(case.get("body"), "").encode()
            media_type = self._string(
                case.get("bodyMediaType"), "application/octet-stream"
            )
            lines.extend(
                (
                    "    actual_body = await read_streaming_blob_async(request.body)",
                    f"    expected_body = {body!r}",
                    *self._body_assertions(media_type),
                )
            )
        return "\n".join(lines)

    def _response_test(
        self,
        operation: Shape,
        target: Shape,
        case: Mapping[str, JSONValue],
        index: int,
    ) -> str:
        operation_name = self.context.symbol_provider.to_symbol(operation).name
        test_name = self._test_name(case, "response", operation, index)
        status = case.get("code", 200)
        if not isinstance(status, int) or isinstance(status, bool):
            raise CodegenError(
                f"Protocol response test code must be an integer: {case}"
            )
        headers = self._header_tuples(case.get("headers"))
        body = self._string(case.get("body"), "").encode()
        expected = self._value(target, case.get("params", {}))
        call = [
            "        operation=operation,",
            "        request=create_test_request(),",
            "        response=response,",
            "        error_registry=operation.error_registry,",
            "        context=TypedProperties(),",
        ]
        lines = [
            "@pytest.mark.asyncio",
            f"async def test_{test_name}() -> None:",
            "    config = Config()",
            "    protocol = config.protocol",
            "    assert protocol is not None",
            f"    operation = models.{operation_name}",
            "    response = HTTPResponse(",
            f"        status={status},",
            f"        fields=tuples_to_fields({headers!r}),",
            f"        body={body!r},",
            "    )",
        ]
        target_name = self.context.symbol_provider.to_symbol(target).name
        if target.has_trait("smithy.api#error"):
            lines.extend(
                (
                    f"    with pytest.raises(models.{target_name}) as caught:",
                    "        await protocol.deserialize_response(",
                    *call,
                    "        )",
                    f"    assert caught.value == {expected}",
                )
            )
        else:
            lines.extend(
                (
                    "    actual = await protocol.deserialize_response(",
                    *call,
                    "    )",
                    f"    assert actual == {expected}",
                )
            )
        return "\n".join(lines)

    def _body_assertions(self, media_type: str) -> tuple[str, ...]:
        if media_type == "application/json" or media_type.endswith("+json"):
            return ("    assert json.loads(actual_body) == json.loads(expected_body)",)
        if media_type == "application/x-www-form-urlencoded":
            return (
                "    assert sorted(parse_qsl(actual_body.decode(), keep_blank_values=True)) == (",
                "        sorted(parse_qsl(expected_body.decode(), keep_blank_values=True))",
                "    )",
            )
        return ("    assert actual_body == expected_body",)

    def _value(self, shape: Shape, value: JSONValue) -> str:
        if value is None:
            return "None"
        if shape.type is ShapeType.STRUCTURE:
            node = self._object(value, shape)
            arguments: list[str] = []
            for member in shape.members:
                if member.name not in node:
                    continue
                target = self.context.model.expect(member.target)
                name = self.context.symbol_provider.to_member_name(
                    member, container=shape
                )
                arguments.append(f"{name}={self._value(target, node[member.name])}")
            symbol = self.context.symbol_provider.to_symbol(shape)
            return f"models.{symbol.name}({', '.join(arguments)})"
        if shape.type is ShapeType.UNION:
            node = self._object(value, shape)
            if len(node) != 1:
                raise CodegenError(
                    f"Protocol test union value must contain one member: {shape.id}"
                )
            member_name, member_value = next(iter(node.items()))
            member = shape.member(member_name)
            target = self.context.model.expect(member.target)
            symbol = self.context.symbol_provider.union_member_symbol(shape, member)
            return f"models.{symbol.name}(value={self._value(target, member_value)})"
        if shape.type is ShapeType.LIST:
            if not isinstance(value, list):
                raise CodegenError(
                    f"Expected a list protocol test value for {shape.id}"
                )
            target = self.context.model.expect(shape.member("member").target)
            return f"[{', '.join(self._value(target, item) for item in value)}]"
        if shape.type is ShapeType.MAP:
            node = self._object(value, shape)
            target = self.context.model.expect(shape.member("value").target)
            entries = ", ".join(
                f"{key!r}: {self._value(target, item)}" for key, item in node.items()
            )
            return f"{{{entries}}}"
        if shape.type is ShapeType.DOCUMENT:
            return f"Document({value!r})"
        if shape.type is ShapeType.BLOB:
            return repr(value.encode() if isinstance(value, str) else value)
        if shape.type is ShapeType.TIMESTAMP:
            if isinstance(value, int | float) and not isinstance(value, bool):
                return f"datetime.fromtimestamp({value!r}, tz=timezone.utc)"
            if isinstance(value, str):
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as error:
                    raise CodegenError(
                        f"Invalid timestamp protocol test value: {value!r}"
                    ) from error
                return f"datetime.fromisoformat({parsed.isoformat()!r})"
        if shape.type in {ShapeType.FLOAT, ShapeType.DOUBLE} and isinstance(value, str):
            special = {"NaN": "nan", "Infinity": "inf", "-Infinity": "-inf"}
            if value in special:
                return f"float({special[value]!r})"
        if shape.type is ShapeType.BIG_DECIMAL:
            return f"Decimal({str(value)!r})"
        if shape.type in {ShapeType.ENUM, ShapeType.INT_ENUM}:
            symbol = self.context.symbol_provider.to_symbol(shape)
            return f"models.{symbol.name}({value!r})"
        return repr(value)

    def _matching(self, value: JSONValue) -> tuple[dict[str, JSONValue], ...]:
        if not isinstance(value, list):
            return ()
        result: list[dict[str, JSONValue]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            if item.get("protocol") != str(self.protocol_id):
                continue
            if item.get("appliesTo") not in {None, "client"}:
                continue
            result.append(item)
        return tuple(result)

    def _response_target(self, case: Mapping[str, JSONValue], fallback: Shape) -> Shape:
        shape_id = case.get("shape")
        if isinstance(shape_id, str):
            return self.context.model.expect(shape_id)
        return fallback

    def _target(self, operation: Shape, key: str) -> Shape | None:
        value = operation.attributes.get(key)
        if not isinstance(value, dict):
            return None
        target_id = value.get("target")
        if not isinstance(target_id, str):
            return None
        target = self.context.model.expect(target_id)
        return target if target in self.context.shapes else None

    def _references(self, operation: Shape, key: str) -> tuple[ShapeID, ...]:
        value = operation.attributes.get(key, [])
        if not isinstance(value, list):
            return ()
        return tuple(
            ShapeID.parse(target)
            for item in value
            if isinstance(item, dict) and isinstance(target := item.get("target"), str)
        )

    def _test_name(
        self,
        case: Mapping[str, JSONValue],
        kind: str,
        operation: Shape,
        index: int,
    ) -> str:
        case_id = case.get("id")
        value = case_id if isinstance(case_id, str) else f"case_{index}"
        return snake_case(f"{value}_{kind}_{operation.id.name}")

    def _object(self, value: JSONValue, shape: Shape) -> dict[str, JSONValue]:
        if not isinstance(value, dict):
            raise CodegenError(f"Expected an object protocol test value for {shape.id}")
        return value

    def _string(self, value: JSONValue, default: str) -> str:
        return value if isinstance(value, str) else default

    def _string_list(self, value: JSONValue) -> list[str]:
        return (
            [item for item in value if isinstance(item, str)]
            if isinstance(value, list)
            else []
        )

    def _string_map(self, value: JSONValue) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {key: item for key, item in value.items() if isinstance(item, str)}

    def _header_tuples(self, value: JSONValue) -> list[tuple[str, str]]:
        return list(self._string_map(value).items())
