"""
This file exists to provide some examples of what serializers and deserializers
should look like for restjson1. It isn't intended to be run per-se, as most of
the data classes are totally empty. See the shape design doc for more info on
what the generated shapes will look like.
"""

import email
import math
import base64
import json
import datetime

from typing import Any, Optional, Generic, TypeVar, Literal

import dateutil


HeadersList = list[tuple[str, str]]


class URL:
    scheme: str
    hostname: str
    port: Optional[int]
    path: str
    query_params: list[tuple[str, str]]


class Request:
    url: URL
    method: str
    headers: HeadersList
    body: Any


class Response:
    status_code: int
    headers: HeadersList
    body: Any


# This actually needs to be implemented. The implementation from
# botocore.utils can likely be copied over.
def percent_encode(given: str) -> str:
    return given


# Non-numeric floats can't be represented in json, so instead we use special string
# representations
def serialize_restjson1_float(given: float) -> float | str:
    if math.isnan(given):
        return "NaN"
    elif math.isinf(given):
        if given < 0:
            return "-Infinity"
        return "Infinity"
    else:
        return given


# I've not bothered to put the actual members here.
class FooOperationInput:
    pass


class FooOperationOutput:
    pass


class Foo:
    pass


class SmithyError(Exception):
    pass


class FooServiceError(SmithyError):
    pass


T = TypeVar("T")


class ApiError(FooServiceError, Generic[T]):
    code: T

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ModeledException(ApiError[Literal["ModeledException"]]):
    code: Literal["ModeledException"] = "ModeledException"

    def __init__(
        self,
        *,
        message: str,
        status: int,
        modeled_member: list[Foo] | None,
    ):
        super().__init__(message)
        self.status = status
        self.modeled_member = modeled_member


class UnknownException(ApiError[Literal["Unknown"]]):
    code: Literal["Unknown"] = "Unknown"


class FooUnionMemberA:
    value: str


class FooUnionMemberB:
    value: Foo


class FooUnionUnknown:
    tag: str


FooUnion = FooUnionMemberA | FooUnionMemberB | FooUnionUnknown


####################
# Serializers
####################


# This is the entry point for serialization. It is ultimately what will get called
# in the serialize middleware for a given operation. Here and in the rest of this
# I've not given the typing for the config and context objects, since that isn't
# well defined yet, but it needs to be present in the final version.
async def _serialize_foo_operation(
    input: FooOperationInput, config, context
) -> Request:
    request = Request()

    # The scheme, hostname, and port will be set by a different middleware.
    url = URL()

    # We'll start with kicking off body serialization. This should usually take up most
    # of serialization time, so starting it now will let us get as much parallel work
    # done as possible.
    body = _serialize_foo_operation_body(input, config, context)

    # Now we start serializing the http bindings. The extent to which we should
    # parallelize here is debatable, so we should actually run some perf tests
    # once we've got a working sample and some reasonable test cases.

    # This is defined in the model, so it'll just be staticly generated here.
    request.method = "POST"

    # These call out to a separate methods just to break out the example. To avoid an
    # excess function call, we should just inline all this logic.
    request.headers = _serialize_foo_operation_headers(input, config, context)
    url.query_params = _serialize_foo_operation_query(input, config, context)
    url.path = _serialize_foo_operation_path(input, config, context)

    # Note: we do not do anything with the host, scheme, or port. These will all be
    # set by some middleware. For AWS clients, this will be based on the AWS endpoint
    # resolver. But there must also be a way for non-aws clients to set a static host.
    # There also is the @endpoint and @hostLabel traits, which can add a prefix to the
    # resolved host. This should also be a separate middleware that gets run after the
    # host is resolved.

    # Now that we've serialized the bindings, lets bring that body in and return the request
    request.body = await body
    return request


async def _serialize_foo_operation_body(
    input: FooOperationInput, config, context
) -> Any:
    # The body of the request is made up of one of two things: a member targeted by the
    # @httpPayload trait, or every member not bound to some other part of the http
    # request.

    # If the httpPayload trait is used, this method will just delegate out to the
    # serializer for that shape, like so:
    # return _serialize_my_http_payload_shape(input, config, context)

    # The only two exceptions are when a string or a blob are targeted. In those cases,
    # the values are used directly. So instead of having this separate method, they can
    # just be assigned in the parent. The trick to those will be handling the various
    # kinds of streaming blobs / strings, but that is a problem for a different part
    # of the client.

    # If the httpPayload trait is not used, this method will create a JSON document
    # representing the remaining members of the request.

    body = {}

    # Required members don't need a check - their presence is asserted by the class
    # constructor. Strings don't need any kind of special handling.
    body["requiredStringMember"] = input.required_string_member

    # Non required members neeed to check
    if not isinstance(input.int_member, _DEFAULT):
        # All of the variously wide int types will be direct assignments like this
        body["intMember"] = input.int_member

    if not isinstance(input.float_member, _DEFAULT):
        # Both float and doubles need special handling
        body["floatMember"] = serialize_restjson1_float(input.float_member)

    if not isinstance(input.bytes_member, _DEFAULT):
        # Bytes need to be base64 encoded
        body["bytesMember"] = base64.b64encode(input.bytes_member).encode("utf-8")

    if not isinstance(input.boolean_member, _DEFAULT):
        # Nothing special needs to be done to format booleans correctly
        body["booleanMember"] = input.boolean_member

    if not isinstance(input.timestamp_member, _DEFAULT):
        # This corresponds to the "epoch-seconds" format of the @timestampFormat trait,
        # which is the default for the body. Note that here we leave it as a number
        # rather than casting it to a string.
        body["timestampMember"] = input.timestamp_member.timestamp()

    if not isinstance(input.document_member, _DEFAULT):
        body["documentMember"] = input.document_member.asdict()

    if not isinstance(input.collection_member, _DEFAULT):
        # When serializing collections
        body["collectionMember"] = _serialize_foo_collection(
            input.collection_member, config, context
        )

    return json.dumps(body)


def _serialize_foo_collection(given: list[Foo], config, context) -> list[Any]:
    # Here we delegate to a struct serializer for the value inside a list comprehension
    return [_serialize_foo_struct(v) for v in input.collection_member]


def _serialize_foo_struct(given: Foo, config, context) -> dict[str, Any]:
    result = {}

    # ser methods for structs will look almost exactly like the method for the http
    # body, the notable difference being the lack of json.dumps at the end.

    if not isinstance(given.customized, _DEFAULT):
        # The @jsonName trait can change the key here. Inside the generated code, you
        # won't be able to tell the difference.
        result["jsonNameAltered"] = given.customized

    if not isinstance(given.string_map, _DEFAULT):
        result["stringMap"] = _serialize_string_map(given.string_map)

    if not isinstance(given.foo_map, _DEFAULT):
        result["fooMap"] = _serialize_foo_map(given.foo_map)

    if not isinstance(given.foo_union, _DEFAULT):
        result["fooUnion"] = _serialize_foo_union(given.foo_union)

    return result


def _serialize_string_map(given: dict[str, str], config, context) -> dict[str, str]:
    # In some cases, nothing will need to be done to a shape to conform it to json.
    # This is also true of lists / sets of strings and integers. These could be
    # collapsed down to simple assignment in the containing structures like we do
    # for plain strings, but it is easier to always treat a given shape the same
    # everywhere. If you have to check whether a given map has a ser method it might
    # get a bit burdensome.
    return given


def _serialize_foo_map(
    given: dict[str, Foo], config, context
) -> dict[str, dict[str, Any]]:
    # Most maps should just use a dict comprehension
    return {k: _serialize_foo_struct(v) for k, v in given.items()}


def _serialize_foo_union(given: FooUnion, config, context) -> dict[str, Any]:
    match given:
        case FooUnionMemberA():
            return {"memberA": given.value}
        case FooUnionMemberB():
            return {"memberB": _serialize_foo_struct(given.value)}
        case FooUnionUnknown():
            raise FooServiceError(
                f"Unknown union member {given.tag} cannot be serialized"
            )
        case _:
            raise FooServiceError(f"Unknown type given for FooUnion: {type(given)}")


# This isn't async because there *usually* won't be that many headers, and they can't
# recurse, so the tradeoff is probably not worth it. This should be tested though.
# See: https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#httpheader-trait
#      https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#httpprefixheaders-trait
def _serialize_foo_operation_headers(
    input: FooOperationInput, config, context
) -> HeadersList:

    # The protocol will define certain static headers that need to be respected.
    headers: HeadersList = [
        # The content type can be affected by what is bound to the payload.
        # See: https://awslabs.github.io/smithy/1.0/spec/aws/aws-restjson1-protocol.html#content-type
        ("content-type", "application/json")
    ]

    # Static headers arise from members with the @httpHeader trait
    if not isinstance(input.string_header, _DEFAULT):
        # Header keys are pulled directly from the model
        headers.append(("amz-string-header", input.string_header))

    if not isinstance(input.boolean_header, _DEFAULT):
        headers.append(
            ("amz-boolean-header", "true" if input.boolean_header else "false")
        )

    if not isinstance(input.number_header, _DEFAULT):
        # If this is a float, we will need to use `serialize_restjson1_float`
        headers.append(("amz-number-header", str(input.number_header)))

    if not isinstance(input.http_date_timestamp, _DEFAULT):
        # This corresponds to the "http-date" format of the @timestampFormat trait,
        # and is the default for headers.
        headers.append(
            (
                "amz-http-date-timestamp-header",
                email.utils.formatdate(input.http_date_timestamp, usegmt=True),
            )
        )

    if not isinstance(input.rfc3339_timestamp_header, _DEFAULT):
        # This corresponds to the "date-time" format of the @timestampFormat trait.
        headers.append(
            ("amz-rfc3339-timestamp-header", input.rfc3339_timestamp_header.isoformat())
        )

    if not isinstance(input.epoch_timestamp_header, _DEFAULT):
        # This corresponds to the "epoch-seconds" format of the @timestampFormat trait.
        headers.append(
            (
                "amz-epoch-timestamp-header",
                str(input.epoch_timestamp_header.timestamp()),
            )
        )

    if not isinstance(input.string_header_list, _DEFAULT) and input.string_header_list:
        _escaped = []
        for entry in input.string_header_list:
            if "," in entry:
                _escaped.apppend(f'"{entry}"')
            else:
                _escaped.append(entry)
        headers.append(("amz-string-header-list", ",".join(_escaped)))

    if not isinstance(input.number_header_list, _DEFAULT) and input.number_header_list:
        # Serizliation of the other header type lists will look like this, with just
        # the string conversion changing. There is no need to escape them.
        headers.append(
            (
                "amz-number-header-list",
                ",".join([str(entry) for entry in input.number_header_list]),
            )
        )

    # Prefix headers arise from members with the @httpPrefixHeaders trait
    if not isinstance(input.prefix_headers, _DEFAULT) and input.prefix_headers:
        for key, value in input.prefix_headers.items():
            # I used a timestamp value here, for other types see above how to convert them
            # to a string. Note that the prefix is statically defined in the model, and can
            # be an empty string.
            headers.append((f"prefix-{key}", value.isoformat()))

            # If the prefix is an empty string, we can simplify to this:
            # headers.append((key, value.isoformat()))

    return headers


# See: https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#httpquery-trait
#      https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#httpqueryparams-trait
def _serialize_foo_operation_query(
    input: FooOperationInput, config, context
) -> list[tuple[str, str]]:

    query: list[tuple[str, str]] = []

    # Static query params arise from members with the @httpQuery trait
    if not isinstance(input.string_query, _DEFAULT):
        # Query keys are pulled directly from the model
        query.append(("string", percent_encode(input.string_query)))

    if not isinstance(input.boolean_query, _DEFAULT):
        query.append(("boolean", "true" if input.boolean_query else "false"))

    if not isinstance(input.number_query, _DEFAULT):
        # If this is a float, we will need to use `serialize_restjson1_float`
        query.append(("number", str(input.number_query)))

    if not isinstance(input.rfc3339_timestamp_header, _DEFAULT):
        # This corresponds to the "date-time" format of the @timestampFormat trait,
        # and is the default for query params.
        query.append(
            (
                "rfc3339-timestamp",
                percent_encode(input.rfc3339_timestamp_header.isoformat()),
            )
        )

    if (
        not isinstance(input.string_query_list, _DEFAULT)
        and not input.string_query_list
    ):
        # Serialization for other major collection types will look like this, where the
        # key is just repeated and the value is serialized as normal.
        query += [("string-list", percent_encode(v)) for v in input.string_query_list]

    # This arises from members with the @httpQueryParams trait
    if not isinstance(input.query_params, _DEFAULT) and not input.query_params:
        query += [
            (percent_encode(key), percent_encode(value))
            for key, value in input.query_params.items()
        ]

    # @httpQueryParams can also target lists of strings
    if (
        not isinstance(input.query_params_list, _DEFAULT)
        and not input.query_params_list
    ):
        for key, values in input.query_params_list:
            query += [(percent_encode(key), percent_encode(v)) for v in values]

    return query


# See: https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#http-trait
#      https://awslabs.github.io/smithy/1.0/spec/core/http-traits.html#httplabel-trait
def _serialize_foo_operation_path(input: FooOperationInput, config, context) -> str:
    # Members bound to the path MUST be required, so we don't have to do any None
    # checks. For the following example, assume the URI pattern is:
    #
    # /foo/{normalLable}/{greedyLabel+}
    #
    # To make things more runtime effecient, we replace the labels in the pattern with
    # normal string formatting symbols so that we can construct the whole thing in one
    # pass.
    return "/foo/%s/%s" % (
        # Path members are all serialized and encoded just as they are in the query,
        # which includes using RFC3339 for timestamps. Collections can't be bound here
        # however.
        percent_encode(input.normal_label),
        # Greedy labels permit using forward slashes, so the encoding implementation
        # must be able to allow that.
        percent_encode(input.greedy_label, ignore_forward_slash=True),
    )


####################
# Deserializers
####################


# Like with the serializer, this method will be the entry point for deserialization.
async def _deserialize_foo_operation(
    response: Response, config, context
) -> FooOperationOutput:
    # The first thing to do is to check if the response is an error, so anything not
    # in the 200 range.
    if response < 200 or response >= 300:
        raise await _deserialize_foo_operation_error(response, config, context)

    parsed_body = _deserialize_foo_operation_body(response, config, context)

    return FooOperationOutput(
        # Services can bind the status code to a member with the @httpStatusCode trait
        status_member=response.status_code,
        # If the body is a streaming blob, we should be able to just directly assign it.
        # The wrapping code that handles the send/receive should ensure the body is always
        # set to a compatible reader.
        # streaming_body = response.body,
        **_deserialize_foo_operation_headers(response.headers, config, context),
        **(await parsed_body),
    )


async def _deserialize_foo_operation_body(
    response: Response, config, context
) -> dict[str, Any]:
    args = {}
    body = _parse_json_body(response)
    if "fooMember" in body:
        args["foo_member"] = _deserialize_foo_struct(body["fooMember"], config, context)
    return args


def _deserialize_foo_operation_headers(
    headers: HeadersList, config, context
) -> dict[str, Any]:
    # Parsing headers is more effort than parsing the body since we don't have json.load
    # to handle a lot of the details for us
    headers_map = _headers_to_map(headers)

    args = {}

    # We can create one of these for each prefix header, matching the param
    # name to the member name to ensure we don't have conflicts.
    prefix_headers = {}
    prefix_list_headers = {}

    for key, value in headers_map.items():
        match key:
            case "amz-string-header":
                args["string_header"] = value
            case "amz-boolean-header":
                args["boolean_header"] = value == "true"
            case "amz-int-header":
                args["int_header"] = int(value)
            case "amz-float-header":
                args["float_header"] = float(value)
            case "timestamp-header":
                args["timestamp_header"] = dateutil.parse(value)
            case "amz-list-header":
                if isinstance(value, list):
                    _list = value
                else:
                    _list = value.split(",")
                args["amz-list-header"] = [int(v) for v in _list]

        # A header can match a prefix AND be in one or more prefixes.
        if key.startswith("prefix"):
            prefix_headers[key] = value

        if key.startswith("listprefix"):
            prefix_list_headers[key] = value

    args["prefix_headers"] = prefix_headers
    args["prefix_list_headers"] = prefix_list_headers

    # If the prefix is empty, we can just directly assign the map
    args["empty_prefix_headers"] = headers_map

    return args


# There's a lesser known feature of headers that we have to account for: keys can
# be duplicated, implying a list. Intermediaries are suppsed to collapse those into
# a single comma-separated header, but we can't guarantee that happened. So here
# we need to handle making this list of tuples into a map.
def _headers_to_map(headers: HeadersList) -> dict[str, str | list[str]]:
    pass


async def _deserialize_foo_operation_error(
    response: Response, config, context
) -> Exception:
    # We need to look at the body to find the code, so here we parse it into json
    # and save that so we can also use it in deserialization without repeating the
    # json parse.
    body = _parse_json_body(response)
    code = _parse_error_code(response, body)

    match code:
        case "ModeledException":
            return _deserialize_modeled_exception(response, body, config, context)
        case _:
            return UnknownException(_parse_error_message(response, body))


def _parse_json_body(response: Response) -> dict[str, Any]:
    # This may need to change depending on what type the body actually is.
    # I'm assuming bytes here.
    return json.loads(response.body.decode("utf8"))


# These two methods can essentially just be straight copied. They're looking
# for the standard code and message locations to try to grab them. This is
# important because they often are put in non-standard locations, or are not
# properly modeled.
def _parse_error_code(response: Response, parsedBody: dict[str, Any]) -> str | None:
    for key, value in response.headers:
        if key.lower() == "x-amzn-errortype":
            return value

    for key, value in parsedBody.items():
        if key.lower() in ["__type", "code"]:
            return value

    return None


def _parse_error_message(response: Response, parsedBody: dict[str, Any]) -> str:
    for key, value in parsedBody.items():
        if key.lower() in ["message", "errormessage"]:
            return value

    return ""


# Parsing an exception generally works exactly like parsing a response body, including
# potential http bindings.
def _deserialize_modeled_exception(
    response: Response, parsedBody: dict[str, Any], config, context
) -> ModeledException:
    args = {
        "message": _parse_error_message(response, parsedBody),
        "status": response.status_code,
    }

    # Optional members go outside the constructor
    if "modeledMember" in parsedBody:
        args["modeled_member"] = _deserialize_foo_collection(
            parsedBody["modeledMember"], config, context
        )

    return ModeledException(**args)


def _deserialize_foo_collection(body: list[Any], config, context) -> list[Foo]:
    return [_deserialize_foo_struct(v, config, context) for v in body]


def _deserialize_foo_struct(body: dict[str, Any], config, context) -> Foo:
    # We need to collect the arguments here to create the object with later.
    args = {}

    # There is no distinction between how required / optional members are handled.
    # They're either present or they aren't. Defaulting will be handled by the
    # constructor.
    if "requiredStringMember" in body:
        # There's nothing to do here so it's a straight assignment
        args["required_string_member"] = body["requiredStringMember"]

    if "intMember" in body:
        # Similar to strings, numeric types don't need any special handling.
        # Bytes, documents, and booleans also look just like this.
        args["int_member"] = body["intMember"]

    if "bytesMember" in body:
        args["bytes_member"] = base64.b64decode(body["bytesMember"])

    # timestamp

    if "httpDateMember" in body:
        # Ideally we shouldn't pull in dateutil, but iirc there isn't a built in parser
        # for the http date format. The other option will be to hand-write one.
        args["http_date_member"] = dateutil.parse(body["httpDateMember"])

    if "epochMember" in body:
        args["epoch_member"] = datetime.datetime.utcfromtimestamp(body["epochMember"])

    if "dateTimeMember" in body:
        args["date_time_member"] = datetime.datetime.fromisoformat(
            body["dateTimeMember"]
        )

    if "unionMember" in body:
        args["union_member"] = _deserialize_foo_union_member(
            body["unionMember"], config, context
        )

    if "collectionMember" in body:
        args["collection_member"] = _deserialize_foo_collection(
            body["collectionMember"], config, context
        )

    if "nestedMember" in body:
        args["nested_member"] = _deserialize_foo_struct(
            body["nestedMember"], config, context
        )

    return Foo(**args)


def _deserialize_foo_union_member(body: dict[str, Any], config, context) -> FooUnion:
    if len(body) != 1:
        raise FooServiceError(
            f"Unions must have exactly 1 member, but found {len(body)}: '{', '.join(body.keys())}'"
        )

    tag, value = list(body.items())[0]
    match tag:
        case "memberA":
            return FooUnionMemberA(value)
        case "memberB":
            return FooUnionMemberB(_deserialize_foo_struct(value, config, context))
        case _:
            return FooUnionUnknown(tag)
