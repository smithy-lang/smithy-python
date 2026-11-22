from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.query"
n1 = "aws.protocoltests.shared"
_s7 = "GreetingStruct"
_s8 = "hi"
_s10 = "key"
_s11 = "value"
_s16 = "smithy.api#timestampFormat"
_s17 = "date-time"
_s19 = "smithy.synthetic#originalShapeId"
_s21 = "smithy.api#output"
_s25 = "smithy.api#input"
_s42 = "myMap"
_s43 = "smithy.api#xmlFlattened"
_s45 = "smithy.api#xmlName"
_s52 = "smithy.api#xmlNamespace"
_s63 = "foo"
_s66 = "member"
_s69 = "item"
_s89 = "data"
_s110 = "epoch-seconds"
_s118 = "nested"
_s130 = "SimpleScalarXmlPropertiesOutput"
_s131 = "aws.protocoltests.query#SimpleScalarXmlPropertiesOutput"
_s132 = "stringValue"
_s133 = "emptyStringValue"
_s134 = "trueBooleanValue"
_s135 = "falseBooleanValue"
_s136 = "byteValue"
_s137 = "shortValue"
_s138 = "integerValue"
_s139 = "longValue"
_s140 = "floatValue"
_s141 = "doubleValue"
_s142 = "DoubleDribble"
_s143 = "StructureListMember"
_s144 = "a"
_s145 = "b"
_s146 = "other"
_s147 = "StructureList"
_s148 = "FooEnumList"
_s149 = "FooEnumSet"
_s150 = "XmlEnumsOutput"
_s151 = "aws.protocoltests.query#XmlEnumsOutput"
_s152 = "fooEnum1"
_s153 = "fooEnum2"
_s154 = "fooEnum3"
_s155 = "fooEnumList"
_s156 = "fooEnumSet"
_s157 = "fooEnumMap"
_s158 = "IntegerEnumList"
_s159 = "IntegerEnumSet"
_s160 = "IntegerEnumMap"
_s161 = "XmlIntEnumsOutput"
_s162 = "aws.protocoltests.query#XmlIntEnumsOutput"
_s163 = "intEnum1"
_s164 = "intEnum2"
_s165 = "intEnum3"
_s166 = "intEnumList"
_s167 = "intEnumSet"
_s168 = "intEnumMap"
_s169 = "XmlMapsOutputMap"
_s170 = "XmlMapsXmlNameOutputMap"
_s171 = "Attribute"
_s172 = "Setting"
_s173 = "XmlMapsXmlNameOutput"
_s174 = "aws.protocoltests.query#XmlMapsXmlNameOutput"
_s175 = "XmlNamespacedList"
_s176 = "XmlNamespaceNested"
_s177 = "values"
_s178 = "XmlNamespacesOutput"
_s179 = "aws.protocoltests.query#XmlNamespacesOutput"
_s180 = "HttpDate"
_s181 = "http-date"
_s182 = "XmlTimestampsOutput"
_s183 = "aws.protocoltests.query#XmlTimestampsOutput"
_s184 = "normal"
_s185 = "dateTime"
_s186 = "dateTimeOnTarget"
_s187 = "epochSeconds"
_s188 = "epochSecondsOnTarget"
_s189 = "httpDate"
_s190 = "httpDateOnTarget"
_s191 = "BooleanList"
_s192 = "IntegerList"
_s193 = "NestedStringList"
_s194 = "StringSet"
_s195 = "TimestampList"
_s197 = "smithy.api#Unit"
_s198 = "EndpointOperationInput"
_s199 = "EndpointOperationOutput"
_s200 = "EndpointWithHostLabelOperationInput"
_s201 = "aws.protocoltests.query#HostLabelInput"
_s202 = "label"
_s203 = "EndpointWithHostLabelOperationOutput"
_s209 = "HostWithPathOperationInput"
_s210 = "HostWithPathOperationOutput"
_s213 = "NoInputAndNoOutputInput"
_s214 = "NoInputAndNoOutputOutput"
_s222 = "SimpleScalarXmlPropertiesInput"
_s223 = "XmlBlobsInput"
_s224 = "XmlBlobsOutput2"
_s225 = "aws.protocoltests.query#XmlBlobsOutput"
_s226 = "XmlEmptyBlobsInput"
_s227 = "XmlEmptyBlobsOutput"
_s228 = "XmlEmptyListsInput"
_s229 = "XmlEmptyListsOutput"
_s230 = "aws.protocoltests.query#XmlListsOutput"
_s231 = "stringList"
_s232 = "stringSet"
_s233 = "integerList"
_s234 = "booleanList"
_s235 = "timestampList"
_s236 = "enumList"
_s237 = "nestedStringList"
_s238 = "renamedListMembers"
_s239 = "renamed"
_s240 = "flattenedList"
_s241 = "flattenedList2"
_s242 = "customName"
_s243 = "flattenedListWithMemberNamespace"
_s244 = "flattenedListWithNamespace"
_s245 = "structureList"
_s246 = "myStructureList"
_s247 = "XmlEmptyMapsInput"
_s248 = "XmlEmptyMapsOutput"
_s249 = "aws.protocoltests.query#XmlMapsOutput"
_s250 = "XmlEnumsInput"
_s251 = "XmlIntEnumsInput"
_s252 = "XmlListsInput"
_s253 = "XmlListsOutput2"
_s254 = "XmlMapsInput"
_s255 = "XmlMapsOutput2"
_s256 = "XmlMapsXmlNameInput"
_s257 = "XmlNamespacesInput"
_s258 = "XmlTimestampsInput"
_s261 = "EndpointOperation"
_s262 = "smithy.api#endpoint"
_s263 = "EndpointWithHostLabelOperation"
_s269 = "HostWithPathOperation"
_s272 = "NoInputAndNoOutput"
_s282 = "SimpleScalarXmlProperties"
_s283 = "XmlBlobs"
_s284 = "XmlEmptyBlobs"
_s285 = "XmlEmptyLists"
_s286 = "XmlEmptyMaps"
_s287 = "XmlEnums"
_s288 = "XmlIntEnums"
_s289 = "XmlLists"
_s290 = "XmlMaps"
_s291 = "XmlMapsXmlName"
_s292 = "XmlNamespaces"
_s293 = "XmlTimestamps"
_s294 = "AwsQuery"
_s295 = "aws.api#service"
_s296 = "aws.auth#sigv4"
_s297 = "aws.protocols#awsQuery"
_s298 = "RecursiveXmlShapesOutputNested1"
_s299 = "RecursiveXmlShapesOutputNested2"
_s300 = "bar"
_s301 = "recursiveMember"
_s302 = "StructArg"
_s303 = "StringArg"
_s304 = "OtherArg"
_s305 = "RecursiveArg"

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s7,
    0,
    (_s8,),
    ((3, 0),),
)

SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s130,
    {_s19: _s131, _s21: None},
    (_s132, _s133, _s134, _s135, _s136, _s137, _s138, _s139, _s140, _s141),
    (
        (3, 0),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s45: _s142}),
    ),
)

SIMPLE_SCALAR_XML_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s222,
    {_s19: _s197, _s25: None},
)

SIMPLE_SCALAR_XML_PROPERTIES: StaticOperationSchema = (
    23,
    n0,
    _s282,
    0,
    SIMPLE_SCALAR_XML_PROPERTIES_INPUT,
    SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT,
    (),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n0,
    _s143,
    0,
    (_s144, _s145),
    ((3, {_s45: _s11}), (3, {_s45: _s146})),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n0,
    _s147,
    0,
    (_s66,),
    ((STRUCTURE_LIST_MEMBER, {_s45: _s69}),),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s148,
    0,
    (_s66,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s149,
    0,
    (_s66,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

XML_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s150,
    {_s19: _s151, _s21: None},
    (_s152, _s153, _s154, _s155, _s156, _s157),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

XML_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s250,
    {_s19: _s197, _s25: None},
)

XML_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s287,
    0,
    XML_ENUMS_INPUT,
    XML_ENUMS_OUTPUT,
    (),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s158,
    0,
    (_s66,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s159,
    0,
    (_s66,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s160,
    0,
    (_s10, _s11),
    ((3, 0), (lambda: schemas.INTEGER_ENUM, 0)),
)

XML_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s161,
    {_s19: _s162, _s21: None},
    (_s163, _s164, _s165, _s166, _s167, _s168),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

XML_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s251,
    {_s19: _s197, _s25: None},
)

XML_INT_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s288,
    0,
    XML_INT_ENUMS_INPUT,
    XML_INT_ENUMS_OUTPUT,
    (),
)

XML_MAPS_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s169,
    0,
    (_s10, _s11),
    ((3, 0), (GREETING_STRUCT, 0)),
)

XML_MAPS_XML_NAME_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s170,
    0,
    (_s10, _s11),
    ((3, {_s45: _s171}), (GREETING_STRUCT, {_s45: _s172})),
)

XML_MAPS_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s173,
    {_s19: _s174, _s21: None},
    (_s42,),
    ((XML_MAPS_XML_NAME_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME_INPUT: StaticSchema = (
    18,
    n0,
    _s256,
    {_s19: _s197, _s25: None},
)

XML_MAPS_XML_NAME: StaticOperationSchema = (
    23,
    n0,
    _s291,
    0,
    XML_MAPS_XML_NAME_INPUT,
    XML_MAPS_XML_NAME_OUTPUT,
    (),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n0,
    _s175,
    0,
    (_s66,),
    ((3, {_s52: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n0,
    _s176,
    {_s52: MappingProxyType({"uri": "http://boo.com"})},
    (_s63, _s177),
    (
        (3, {_s52: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s52: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NAMESPACES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s178,
    {_s52: MappingProxyType({"uri": "http://foo.com"}), _s19: _s179, _s21: None},
    (_s118,),
    ((XML_NAMESPACE_NESTED, 0),),
)

XML_NAMESPACES_INPUT: StaticSchema = (
    18,
    n0,
    _s257,
    {_s19: _s197, _s25: None},
)

XML_NAMESPACES: StaticOperationSchema = (
    23,
    n0,
    _s292,
    0,
    XML_NAMESPACES_INPUT,
    XML_NAMESPACES_OUTPUT,
    (),
)

HTTP_DATE: StaticSchema = (
    4,
    n1,
    _s180,
    {_s16: _s181},
)

XML_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s182,
    {_s19: _s183, _s21: None},
    (_s184, _s185, _s186, _s187, _s188, _s189, _s190),
    (
        (4, 0),
        (4, {_s16: _s17}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s16: _s110}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s16: _s181}),
        (HTTP_DATE, 0),
    ),
)

XML_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s258,
    {_s19: _s197, _s25: None},
)

XML_TIMESTAMPS: StaticOperationSchema = (
    23,
    n0,
    _s293,
    0,
    XML_TIMESTAMPS_INPUT,
    XML_TIMESTAMPS_OUTPUT,
    (),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n1,
    _s191,
    0,
    (_s66,),
    ((2, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n1,
    _s192,
    0,
    (_s66,),
    ((7, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s193,
    0,
    (_s66,),
    ((lambda: schemas.STRING_LIST, 0),),
)

STRING_SET: StaticSchema = (
    16,
    n1,
    _s194,
    0,
    (_s66,),
    ((3, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n1,
    _s195,
    0,
    (_s66,),
    ((4, 0),),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s198,
    {_s19: _s197, _s25: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s199,
    {_s19: _s197, _s21: None},
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s261,
    {_s262: MappingProxyType({"hostPrefix": "foo."})},
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s200,
    {_s19: _s201, _s25: None},
    (_s202,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s203,
    {_s19: _s197, _s21: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s263,
    {_s262: MappingProxyType({"hostPrefix": "foo.{label}."})},
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

HOST_WITH_PATH_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s209,
    {_s19: _s197, _s25: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s210,
    {_s19: _s197, _s21: None},
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s269,
    0,
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

NO_INPUT_AND_NO_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s213,
    {_s19: _s197, _s25: None},
)

NO_INPUT_AND_NO_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s214,
    {_s19: _s197, _s21: None},
)

NO_INPUT_AND_NO_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s272,
    0,
    NO_INPUT_AND_NO_OUTPUT_INPUT,
    NO_INPUT_AND_NO_OUTPUT_OUTPUT,
    (),
)

XML_BLOBS_INPUT: StaticSchema = (
    18,
    n0,
    _s223,
    {_s19: _s197, _s25: None},
)

XML_BLOBS_OUTPUT2: StaticSchema = (
    18,
    n0,
    _s224,
    {_s19: _s225, _s21: None},
    (_s89,),
    ((1, 0),),
)

XML_BLOBS: StaticOperationSchema = (
    23,
    n0,
    _s283,
    0,
    XML_BLOBS_INPUT,
    XML_BLOBS_OUTPUT2,
    (),
)

XML_EMPTY_BLOBS_INPUT: StaticSchema = (
    18,
    n0,
    _s226,
    {_s19: _s197, _s25: None},
)

XML_EMPTY_BLOBS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s227,
    {_s19: _s225, _s21: None},
    (_s89,),
    ((1, 0),),
)

XML_EMPTY_BLOBS: StaticOperationSchema = (
    23,
    n0,
    _s284,
    0,
    XML_EMPTY_BLOBS_INPUT,
    XML_EMPTY_BLOBS_OUTPUT,
    (),
)

XML_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s228,
    {_s19: _s197, _s25: None},
)

XML_EMPTY_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s229,
    {_s19: _s230, _s21: None},
    (
        _s231,
        _s232,
        _s233,
        _s234,
        _s235,
        _s236,
        _s166,
        _s237,
        _s238,
        _s240,
        _s241,
        _s243,
        _s244,
        _s245,
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
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s45: _s239}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s43: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s43: None, _s45: _s242}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s43: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s43: None}),
        (STRUCTURE_LIST, {_s45: _s246}),
    ),
)

XML_EMPTY_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s285,
    0,
    XML_EMPTY_LISTS_INPUT,
    XML_EMPTY_LISTS_OUTPUT,
    (),
)

XML_EMPTY_MAPS_INPUT: StaticSchema = (
    18,
    n0,
    _s247,
    {_s19: _s197, _s25: None},
)

XML_EMPTY_MAPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s248,
    {_s19: _s249, _s21: None},
    (_s42,),
    ((XML_MAPS_OUTPUT_MAP, 0),),
)

XML_EMPTY_MAPS: StaticOperationSchema = (
    23,
    n0,
    _s286,
    0,
    XML_EMPTY_MAPS_INPUT,
    XML_EMPTY_MAPS_OUTPUT,
    (),
)

XML_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s252,
    {_s19: _s197, _s25: None},
)

XML_LISTS_OUTPUT2: StaticSchema = (
    18,
    n0,
    _s253,
    {_s19: _s230, _s21: None},
    (
        _s231,
        _s232,
        _s233,
        _s234,
        _s235,
        _s236,
        _s166,
        _s237,
        _s238,
        _s240,
        _s241,
        _s243,
        _s244,
        _s245,
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
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s45: _s239}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s43: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s43: None, _s45: _s242}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s43: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s43: None}),
        (STRUCTURE_LIST, {_s45: _s246}),
    ),
)

XML_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s289,
    0,
    XML_LISTS_INPUT,
    XML_LISTS_OUTPUT2,
    (),
)

XML_MAPS_INPUT: StaticSchema = (
    18,
    n0,
    _s254,
    {_s19: _s197, _s25: None},
)

XML_MAPS_OUTPUT2: StaticSchema = (
    18,
    n0,
    _s255,
    {_s19: _s249, _s21: None},
    (_s42,),
    ((XML_MAPS_OUTPUT_MAP, 0),),
)

XML_MAPS: StaticOperationSchema = (
    23,
    n0,
    _s290,
    0,
    XML_MAPS_INPUT,
    XML_MAPS_OUTPUT2,
    (),
)

AWS_QUERY: StaticSchema = (
    21,
    n0,
    _s294,
    {
        _s295: MappingProxyType({"sdkId": "Query Protocol"}),
        _s296: MappingProxyType({"name": "awsquery"}),
        _s297: None,
        _s52: MappingProxyType({"uri": "https://example.com/"}),
    },
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED1: StaticSchema = (
    18,
    n0,
    _s298,
    0,
    (_s63, _s118),
    ((3, 0), (lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED2, 0)),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED2: StaticSchema = (
    18,
    n0,
    _s299,
    0,
    (_s300, _s301),
    ((3, 0), (RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0)),
)

STRUCT_ARG: StaticSchema = (
    18,
    n0,
    _s302,
    0,
    (_s303, _s304, _s305),
    ((3, 0), (2, 0), (lambda: STRUCT_ARG, 0)),
)
