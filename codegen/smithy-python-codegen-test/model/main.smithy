$version: "2.0"

namespace example.weather

use smithy.test#httpRequestTests
use smithy.test#httpResponseTests
use smithy.waiters#waitable
use aws.protocols#restJson1

/// Provides weather forecasts.
@restJson1
@fakeProtocol
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "pageSize")
@httpApiKeyAuth(name: "weather-auth", in: "header")
service Weather {
    version: "2006-03-01"
    resources: [City]
    operations: [GetCurrentTime]
}

resource City {
    identifiers: { cityId: CityId }
    read: GetCity
    list: ListCities
    resources: [Forecast, CityImage]
    operations: [GetCityAnnouncements]
}

resource Forecast {
    identifiers: { cityId: CityId }
    read: GetForecast
}

resource CityImage {
    identifiers: { cityId: CityId }
    read: GetCityImage
}

// "pattern" is a trait.
@pattern("^[A-Za-z0-9 ]+$")
string CityId

@readonly
@suppress(["WaitableTraitInvalidErrorType"])
@waitable(
    CityExists: {
        acceptors: [
            // Fail-fast if the thing transitions to a "failed" state.
            {
                state: "failure",
                matcher: {
                    errorType: "NoSuchResource"
                }
            },
            // Fail-fast if the thing transitions to a "failed" state.
            {
                state: "failure",
                matcher: {
                    errorType: "UnModeledError"
                }
            },
            // Succeed when the city image value is not empty i.e. enters into a "success" state.
            {
                state: "success",
                matcher: {
                    success: true
                }
            },
            // Retry if city id input is of same length as city name in output
            {
                state: "retry",
                matcher: {
                    inputOutput: {
                        path: "length(input.cityId) == length(output.name)",
                        comparator: "booleanEquals",
                        expected: "true",
                    }
                }
            },
            // Success if city name in output is seattle
            {
                state: "success",
                matcher: {
                    output: {
                        path: "name",
                        comparator: "stringEquals",
                        expected: "seattle",
                    }
                }
            }
        ]
    }
)
@http(method: "GET", uri: "/cities/{cityId}")
operation GetCity {
    input := {
        // "cityId" provides the identifier for the resource and
        // has to be marked as required.
        @required
        @httpLabel
        cityId: CityId
    }
    output := {
        // "required" is used on output to indicate if the service
        // will always provide a value for the member.
        @required
        name: String

        @required
        coordinates: CityCoordinates

        city: CitySummary

        cityData: JsonString
        binaryCityData: JsonBlob
    }
    errors: [NoSuchResource, EmptyError]
}

// Tests that HTTP protocol tests are generated.
apply GetCity @httpRequestTests([
    {
        id: "WriteGetCityAssertions",
        documentation: "Does something",
        protocol: "example.weather#fakeProtocol",
        method: "GET",
        uri: "/cities/123",
        body: "",
        params: {
            cityId: "123"
        }
    }
])

apply GetCity @httpResponseTests([
    {
        id: "WriteGetCityResponseAssertions",
        documentation: "Does something",
        protocol: "example.weather#fakeProtocol",
        code: 200,
        body: """
            {
                "name": "Seattle",
                "coordinates": {
                    "latitude": 12.34,
                    "longitude": -56.78
                },
                "city": {
                    "cityId": "123",
                    "name": "Seattle",
                    "number": "One",
                    "case": "Upper"
                }
            }""",
        bodyMediaType: "application/json",
        params: {
            name: "Seattle",
            coordinates: {
                latitude: 12.34,
                longitude: -56.78
            },
            city: {
                cityId: "123",
                name: "Seattle",
                number: "One",
                case: "Upper"
            }
        }
    }
])

@mediaType("application/json")
string JsonString

@mediaType("application/json")
blob JsonBlob

// This structure is nested within GetCityOutput.
structure CityCoordinates {
    @required
    latitude: Float

    @required
    longitude: Float
}

/// Error encountered when no resource could be found.
@error("client")
@httpError(404)
structure NoSuchResource {
    /// The type of resource that was not found.
    @required
    resourceType: String

    message: String
}

apply NoSuchResource @httpResponseTests([
    {
        id: "WriteNoSuchResourceAssertions",
        documentation: "Does something",
        protocol: "example.weather#fakeProtocol",
        code: 404,
        body: """
            {
                "resourceType": "City",
                "message": "Your custom message"
            }""",
        bodyMediaType: "application/json",
        params: {
            resourceType: "City",
            message: "Your custom message"
        }
    }
])

// This will have a synthetic message member added to it, even
// though it doesn't actually have one.
@error("client")
@httpError(400)
structure EmptyError {}

// The paginated trait indicates that the operation may
// return truncated results.
@readonly
@paginated(items: "items")
@waitable(
    "ListContainsCity": {
        acceptors: [
            // failure in case all items returned match to seattle
            {
                state: "failure",
                matcher: {
                    output: {
                        path: "items[].name",
                        comparator: "allStringEquals",
                        expected: "seattle",
                    }
                }
            },
            // success in case any items returned match to NewYork
            {
                state: "success",
                matcher: {
                    output: {
                        path: "items[].name",
                        comparator: "anyStringEquals",
                        expected: "NewYork",
                    }
                }
            }
        ]
    }
)
@http(method: "GET", uri: "/cities")
operation ListCities {
    input := {
        @httpQuery("nextToken")
        nextToken: String

        @httpQuery("aString")
        aString: String

        @httpQuery("someEnum")
        someEnum: StringYesNo

        @httpQuery("pageSize")
        pageSize: Integer
    },
    output := {
        nextToken: String

        someEnum: StringYesNo
        aString: String
        defaults: Defaults
        escaping: MemberEscaping
        escapeTrue: True
        escapeFalse: False
        escapeNone: None

        @required
        items: CitySummaries
        sparseItems: SparseCitySummaries

        mutual: MutuallyRecursiveA
    }
}

apply ListCities @httpRequestTests([
    {
        id: "WriteListCitiesAssertions"
        documentation: "Does something"
        protocol: "example.weather#fakeProtocol"
        method: "GET"
        uri: "/cities"
        body: ""
        queryParams: ["pageSize=50"]
        forbidQueryParams: ["nextToken"]
        params: {
            pageSize: 50
        }
    }
])

structure Defaults {
    @required
    requiredBool: Boolean
    optionalBool: Boolean
    defaultTrue: Boolean = true
    defaultFalse: Boolean = false
    @required
    requiredDefaultBool: Boolean = true

    @required
    requiredStr: String
    optionalStr: String
    defaultString: String = "spam"
    @required
    requiredDefaultStr: String = "eggs"

    @required
    requiredInt: Integer
    optionalInt: Integer
    defaultInt: Integer = 42
    @required
    requiredDefaultInt: Integer = 42

    @required
    requiredFloat: Float
    optionalFloat: Float
    defaultFloat: Float = 4.2
    @required
    requiredDefaultFloat: Float = 4.2

    @required
    requiredBlob: Blob
    optionalBlob: Blob
    defaultBlob: Blob = "c3BhbQ=="
    @required
    requiredDefaultBlob: Blob = "c3BhbQ=="

    // timestamp
    @required
    requiredTimestamp: Timestamp
    optionalTimestamp: Timestamp
    defaultImplicitDateTime: Timestamp = "2011-12-03T10:15:30Z"
    defaultImplicitEpochTime: Timestamp = 4.2
    defaultExplicitDateTime: DateTime = "2011-12-03T10:15:30Z"
    defaultExplicitEpochTime: EpochSeconds = 4.2
    defaultExplicitHttpTime: HttpDate = "Tue, 3 Jun 2008 11:05:30 GMT"
    @required
    requiredDefaultTimestamp: Timestamp = 4.2

    @required
    requiredList: StringList
    optionalList: StringList
    defaultList: StringList = []
    @required
    requiredDefaultList: StringList = []

    @required
    requiredMap: StringMap
    optionalMap: StringMap
    defaultMap: StringMap = {}
    @required
    requiredDefaultMap: StringMap = {}

    @required
    requiredDocument: Document
    optionalDocument: Document
    defaultNullDocument: Document = null
    defaultNumberDocument: Document = 42
    defaultStringDocument: Document = "spam"
    defaultBooleanDocument: Document = true
    defaultListDocument: Document = []
    defaultMapDocument: Document = {}
    @required
    requiredDefaultDocument: Document = "eggs"
}

// This structure has members that need to be escaped.
structure MemberEscaping {
    // This first set of member names are all reserved words that are a syntax
    // error to use as identifiers. A full list of these can be found here:
    // https://docs.python.org/3/reference/lexical_analysis.html#keywords
    and: String
    as: String
    assert: String
    async: String
    await: String
    break: String
    class: String
    continue: String
    def: String
    del: String
    elif: String
    else: String
    except: String
    finally: String
    for: String
    from: String
    global: String
    if: String
    import: String
    in: String
    is: String
    lambda: String
    nonlocal: String
    not: String
    or: String
    pass: String
    raise: String
    return: String
    try: String
    while: String
    with: String
    yield: String

    // These are built-in types, but not reserved words. They can be shadowed,
    // but the shadowing naturally makes it impossible to use them later in
    // scope. A listing of these can be found here:
    // https://docs.python.org/3/library/stdtypes.html
    bool: Boolean
    dict: StringMap
    float: Float
    int: Integer
    list: StringList
    str: String
    bytes: Blob
    bytearray: Blob

    // We don't actually use these, but they're here for completeness.
    complex: Float
    tuple: StringList
    range: StringList
    memoryview: Blob
    set: StringList
    frozenset: StringList
}

// These would result in class names that produce syntax errors since they're
// reserved words.
structure True {}
structure False {}
structure None {}

@timestampFormat("date-time")
timestamp DateTime

@timestampFormat("epoch-seconds")
timestamp EpochSeconds

@timestampFormat("http-date")
timestamp HttpDate

list StringList {
    member: String
}

structure MutuallyRecursiveA {
    mutual: MutuallyRecursiveB
}

structure MutuallyRecursiveB {
    mutual: MutuallyRecursiveA
}

// CitySummaries is a list of CitySummary structures.
list CitySummaries {
    member: CitySummary
}

// CitySummaries is a sparse list of CitySummary structures.
@sparse
list SparseCitySummaries {
    member: CitySummary
}

// CitySummary contains a reference to a City.
@references([{resource: City}])
structure CitySummary {
    @required
    cityId: CityId

    @required
    name: String

    number: String
    case: String
}

@readonly
@http(method: "GET", uri: "/current-time")
operation GetCurrentTime {
    output := {
        @required
        time: Timestamp
    }
}

@readonly
@http(method: "GET", uri: "/cities/{cityId}/forecast")
operation GetForecast {
    input := {
        @required
        @httpLabel
        cityId: CityId
    },
    output := {
        chanceOfRain: Float
        precipitation: Precipitation
    }
}

union Precipitation {
    rain: PrimitiveBoolean
    sleet: PrimitiveBoolean
    hail: StringMap
    snow: StringYesNo
    mixed: IntYesNo
    other: OtherStructure
    blob: Blob
    foo: example.weather.nested#Foo
    baz: example.weather.nested.more#Baz
}

structure OtherStructure {}

enum StringYesNo {
    YES
    NO
}

intEnum IntYesNo {
    YES = 1
    NO = 2
}

map StringMap {
    key: String
    value: String
}

@readonly
@suppress(["HttpMethodSemantics"])
@http(method: "POST", uri: "/cities/{cityId}/image")
operation GetCityImage {
    input := {
        @required @httpLabel
        cityId: CityId

        @required
        imageType: ImageType
    }
    output := {
        @httpPayload
        @required
        image: CityImageData
    }
    errors: [NoSuchResource]
}

union ImageType {
    raw: Boolean
    png: PNGImage
}

structure PNGImage {
    @required
    height: Integer

    @required
    width: Integer
}

@streaming
blob CityImageData

@readonly
@http(method: "GET", uri: "/cities/{cityId}/announcements")
operation GetCityAnnouncements {
    input := {
        @required
        @httpLabel
        cityId: CityId
    }
    output := {
        @httpHeader("x-last-updated")
        lastUpdated: Timestamp

        @httpPayload
        announcements: Announcements
    }
    errors: [NoSuchResource]
}

@streaming
union Announcements {
    police: Message
    fire: Message
    health: Message
}

structure Message {
    message: String
    author: String
}

// Define a fake protocol trait for use.
@trait
@protocolDefinition
structure fakeProtocol {}
