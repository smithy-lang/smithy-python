from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.ec2"
n1 = "aws.protocoltests.shared"
_s8 = "smithy.api#timestampFormat"
_s9 = "date-time"
_s11 = "smithy.synthetic#originalShapeId"
_s13 = "smithy.api#output"
_s17 = "smithy.api#input"
_s26 = "smithy.api#xmlName"
_s29 = "foo"
_s33 = "smithy.api#xmlNamespace"
_s34 = "member"
_s37 = "item"
_s50 = "data"
_s65 = "epoch-seconds"
_s73 = "nested"
_s77 = "smithy.api#enumValue"
_s120 = "value"
_s123 = "StructureList"
_s124 = "FooEnumList"
_s125 = "FooEnumSet"
_s126 = "FooEnumMap"
_s127 = "key"
_s128 = "XmlEnumsOutput"
_s129 = "aws.protocoltests.ec2#XmlEnumsOutput"
_s130 = "fooEnum1"
_s131 = "fooEnum2"
_s132 = "fooEnum3"
_s133 = "fooEnumList"
_s134 = "fooEnumSet"
_s135 = "fooEnumMap"
_s136 = "IntegerEnum"
_s137 = "A"
_s138 = "B"
_s139 = "C"
_s140 = "IntegerEnumList"
_s141 = "IntegerEnumSet"
_s142 = "IntegerEnumMap"
_s143 = "XmlIntEnumsOutput"
_s144 = "aws.protocoltests.ec2#XmlIntEnumsOutput"
_s145 = "intEnum1"
_s146 = "intEnum2"
_s147 = "intEnum3"
_s148 = "intEnumList"
_s149 = "intEnumSet"
_s150 = "intEnumMap"
_s151 = "XmlNamespacedList"
_s152 = "XmlNamespaceNested"
_s153 = "values"
_s154 = "XmlNamespacesOutput"
_s155 = "aws.protocoltests.ec2#XmlNamespacesOutput"
_s156 = "HttpDate"
_s157 = "http-date"
_s158 = "XmlTimestampsOutput"
_s159 = "aws.protocoltests.ec2#XmlTimestampsOutput"
_s160 = "normal"
_s161 = "dateTime"
_s162 = "dateTimeOnTarget"
_s163 = "epochSeconds"
_s164 = "epochSecondsOnTarget"
_s165 = "httpDate"
_s166 = "httpDateOnTarget"
_s167 = "BooleanList"
_s168 = "IntegerList"
_s169 = "NestedStringList"
_s170 = "StringSet"
_s171 = "TimestampList"
_s173 = "smithy.api#Unit"
_s174 = "EndpointOperationInput"
_s175 = "EndpointOperationOutput"
_s176 = "EndpointWithHostLabelOperationInput"
_s177 = "aws.protocoltests.ec2#HostLabelInput"
_s178 = "label"
_s179 = "EndpointWithHostLabelOperationOutput"
_s182 = "HostWithPathOperationInput"
_s183 = "HostWithPathOperationOutput"
_s194 = "XmlBlobsInput"
_s195 = "XmlBlobsOutput2"
_s196 = "aws.protocoltests.ec2#XmlBlobsOutput"
_s197 = "XmlEmptyBlobsInput"
_s198 = "XmlEmptyBlobsOutput"
_s199 = "XmlEmptyListsInput"
_s200 = "XmlEmptyListsOutput"
_s201 = "aws.protocoltests.ec2#XmlListsOutput"
_s202 = "stringList"
_s203 = "stringSet"
_s204 = "integerList"
_s205 = "booleanList"
_s206 = "timestampList"
_s207 = "enumList"
_s208 = "nestedStringList"
_s209 = "renamedListMembers"
_s210 = "renamed"
_s211 = "flattenedList"
_s212 = "smithy.api#xmlFlattened"
_s213 = "flattenedList2"
_s214 = "customName"
_s215 = "flattenedListWithMemberNamespace"
_s216 = "flattenedListWithNamespace"
_s217 = "structureList"
_s218 = "myStructureList"
_s219 = "XmlEnumsInput"
_s220 = "XmlIntEnumsInput"
_s221 = "XmlListsInput"
_s222 = "XmlListsOutput2"
_s223 = "XmlNamespacesInput"
_s224 = "XmlTimestampsInput"
_s227 = "EndpointOperation"
_s228 = "smithy.api#endpoint"
_s229 = "EndpointWithHostLabelOperation"
_s232 = "HostWithPathOperation"
_s244 = "XmlBlobs"
_s245 = "XmlEmptyBlobs"
_s246 = "XmlEmptyLists"
_s247 = "XmlEnums"
_s248 = "XmlIntEnums"
_s249 = "XmlLists"
_s250 = "XmlNamespaces"
_s251 = "XmlTimestamps"
_s252 = "AwsEc2"
_s253 = "aws.api#service"
_s254 = "aws.auth#sigv4"
_s255 = "aws.protocols#ec2Query"
_s256 = "RecursiveXmlShapesOutputNested1"
_s257 = "RecursiveXmlShapesOutputNested2"
_s258 = "bar"
_s259 = "recursiveMember"
_s260 = "StructArg"
_s261 = "StringArg"
_s262 = "OtherArg"
_s263 = "RecursiveArg"

STRUCTURE_LIST: StaticSchema = (
    16,
    n0,
    _s123,
    0,
    (_s34,),
    ((lambda: schemas.STRUCTURE_LIST_MEMBER, {_s26: _s37}),),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s124,
    0,
    (_s34,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s125,
    0,
    (_s34,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s126,
    0,
    (_s127, _s120),
    ((3, 0), (lambda: schemas.FOO_ENUM, 0)),
)

XML_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s128,
    {_s11: _s129, _s13: None},
    (_s130, _s131, _s132, _s133, _s134, _s135),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

XML_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s219,
    {_s11: _s173, _s17: None},
)

XML_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s247,
    0,
    XML_ENUMS_INPUT,
    XML_ENUMS_OUTPUT,
    (),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s136,
    0,
    (_s137, _s138, _s139),
    ((-1, {_s77: 1}), (-1, {_s77: 2}), (-1, {_s77: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s140,
    0,
    (_s34,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s141,
    0,
    (_s34,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s142,
    0,
    (_s127, _s120),
    ((3, 0), (INTEGER_ENUM, 0)),
)

XML_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s143,
    {_s11: _s144, _s13: None},
    (_s145, _s146, _s147, _s148, _s149, _s150),
    (
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

XML_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s220,
    {_s11: _s173, _s17: None},
)

XML_INT_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s248,
    0,
    XML_INT_ENUMS_INPUT,
    XML_INT_ENUMS_OUTPUT,
    (),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n0,
    _s151,
    0,
    (_s34,),
    ((3, {_s33: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n0,
    _s152,
    {_s33: MappingProxyType({"uri": "http://foo.com"})},
    (_s29, _s153),
    (
        (3, {_s33: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s33: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NAMESPACES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s154,
    {_s33: MappingProxyType({"uri": "http://foo.com"}), _s11: _s155, _s13: None},
    (_s73,),
    ((XML_NAMESPACE_NESTED, 0),),
)

XML_NAMESPACES_INPUT: StaticSchema = (
    18,
    n0,
    _s223,
    {_s11: _s173, _s17: None},
)

XML_NAMESPACES: StaticOperationSchema = (
    23,
    n0,
    _s250,
    0,
    XML_NAMESPACES_INPUT,
    XML_NAMESPACES_OUTPUT,
    (),
)

HTTP_DATE: StaticSchema = (
    4,
    n1,
    _s156,
    {_s8: _s157},
)

XML_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s158,
    {_s11: _s159, _s13: None},
    (_s160, _s161, _s162, _s163, _s164, _s165, _s166),
    (
        (4, 0),
        (4, {_s8: _s9}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s8: _s65}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s8: _s157}),
        (HTTP_DATE, 0),
    ),
)

XML_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s224,
    {_s11: _s173, _s17: None},
)

XML_TIMESTAMPS: StaticOperationSchema = (
    23,
    n0,
    _s251,
    0,
    XML_TIMESTAMPS_INPUT,
    XML_TIMESTAMPS_OUTPUT,
    (),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n1,
    _s167,
    0,
    (_s34,),
    ((2, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n1,
    _s168,
    0,
    (_s34,),
    ((7, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s169,
    0,
    (_s34,),
    ((lambda: schemas.STRING_LIST, 0),),
)

STRING_SET: StaticSchema = (
    16,
    n1,
    _s170,
    0,
    (_s34,),
    ((3, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n1,
    _s171,
    0,
    (_s34,),
    ((4, 0),),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s174,
    {_s11: _s173, _s17: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s175,
    {_s11: _s173, _s13: None},
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s227,
    {_s228: MappingProxyType({"hostPrefix": "foo."})},
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s176,
    {_s11: _s177, _s17: None},
    (_s178,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s179,
    {_s11: _s173, _s13: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s229,
    {_s228: MappingProxyType({"hostPrefix": "foo.{label}."})},
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

HOST_WITH_PATH_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s182,
    {_s11: _s173, _s17: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s183,
    {_s11: _s173, _s13: None},
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s232,
    0,
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

XML_BLOBS_INPUT: StaticSchema = (
    18,
    n0,
    _s194,
    {_s11: _s173, _s17: None},
)

XML_BLOBS_OUTPUT2: StaticSchema = (
    18,
    n0,
    _s195,
    {_s11: _s196, _s13: None},
    (_s50,),
    ((1, 0),),
)

XML_BLOBS: StaticOperationSchema = (
    23,
    n0,
    _s244,
    0,
    XML_BLOBS_INPUT,
    XML_BLOBS_OUTPUT2,
    (),
)

XML_EMPTY_BLOBS_INPUT: StaticSchema = (
    18,
    n0,
    _s197,
    {_s11: _s173, _s17: None},
)

XML_EMPTY_BLOBS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s198,
    {_s11: _s196, _s13: None},
    (_s50,),
    ((1, 0),),
)

XML_EMPTY_BLOBS: StaticOperationSchema = (
    23,
    n0,
    _s245,
    0,
    XML_EMPTY_BLOBS_INPUT,
    XML_EMPTY_BLOBS_OUTPUT,
    (),
)

XML_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s199,
    {_s11: _s173, _s17: None},
)

XML_EMPTY_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s200,
    {_s11: _s201, _s13: None},
    (
        _s202,
        _s203,
        _s204,
        _s205,
        _s206,
        _s207,
        _s148,
        _s208,
        _s209,
        _s211,
        _s213,
        _s215,
        _s216,
        _s217,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (STRING_SET, 0),
        (INTEGER_LIST, 0),
        (BOOLEAN_LIST, 0),
        (TIMESTAMP_LIST, 0),
        (FOO_ENUM_LIST, 0),
        (INTEGER_ENUM_LIST, 0),
        (NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s26: _s210}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s212: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s212: None, _s26: _s214}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s212: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s212: None}),
        (STRUCTURE_LIST, {_s26: _s218}),
    ),
)

XML_EMPTY_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s246,
    0,
    XML_EMPTY_LISTS_INPUT,
    XML_EMPTY_LISTS_OUTPUT,
    (),
)

XML_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s221,
    {_s11: _s173, _s17: None},
)

XML_LISTS_OUTPUT2: StaticSchema = (
    18,
    n0,
    _s222,
    {_s11: _s201, _s13: None},
    (
        _s202,
        _s203,
        _s204,
        _s205,
        _s206,
        _s207,
        _s148,
        _s208,
        _s209,
        _s211,
        _s213,
        _s215,
        _s216,
        _s217,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (STRING_SET, 0),
        (INTEGER_LIST, 0),
        (BOOLEAN_LIST, 0),
        (TIMESTAMP_LIST, 0),
        (FOO_ENUM_LIST, 0),
        (INTEGER_ENUM_LIST, 0),
        (NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s26: _s210}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s212: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s212: None, _s26: _s214}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s212: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s212: None}),
        (STRUCTURE_LIST, {_s26: _s218}),
    ),
)

XML_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s249,
    0,
    XML_LISTS_INPUT,
    XML_LISTS_OUTPUT2,
    (),
)

AWS_EC2: StaticSchema = (
    21,
    n0,
    _s252,
    {
        _s253: MappingProxyType({"sdkId": "EC2 Protocol"}),
        _s254: MappingProxyType({"name": "ec2query"}),
        _s255: None,
        _s33: MappingProxyType({"uri": "https://example.com/"}),
    },
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED1: StaticSchema = (
    18,
    n0,
    _s256,
    0,
    (_s29, _s73),
    ((3, 0), (lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED2, 0)),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED2: StaticSchema = (
    18,
    n0,
    _s257,
    0,
    (_s258, _s259),
    ((3, 0), (RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0)),
)

STRUCT_ARG: StaticSchema = (
    18,
    n0,
    _s260,
    0,
    (_s261, _s262, _s263),
    ((3, 0), (2, 0), (lambda: STRUCT_ARG, 0)),
)
