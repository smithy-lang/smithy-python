$version: "2.0"

namespace example.weather

use smithy.test#httpRequestTests
use smithy.test#httpResponseTests
use smithy.waiters#waitable

/// Provides weather forecasts.
@fakeProtocol
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "pageSize")
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
    errors: [NoSuchResource]
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

        @httpQuery("defaultBool")
        defaultBool: DefaultBool

        @httpQuery("boxedBool")
        boxedBool: Boolean

        @httpQuery("defaultNumber")
        defaultNumber: DefaultInteger

        @httpQuery("boxedNumber")
        boxedNumber: Integer

        @httpQuery("someEnum")
        someEnum: StringYesNo

        @httpQuery("pageSize")
        pageSize: Integer
    },
    output := {
        nextToken: String

        someEnum: StringYesNo
        aString: String
        defaultBool: DefaultBool
        boxedBool: Boolean
        defaultNumber: DefaultInteger
        boxedNumber: Integer

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

integer DefaultInteger
boolean DefaultBool

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
    raw: DefaultBool
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
