from dataclasses import dataclass
from enum import IntEnum, StrEnum

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.response import ResponseMetadata
from smithy_core.types import UnknownEnumMixin

from ..models import (
    EventStream as ___models_EventStream,
)
from ..models import (
    EventStreamExample as ___models_EventStreamExample,
)
from ..models import (
    EventStreamUnknown as ___models_EventStreamUnknown,
)
from ..models import (
    ExampleValue as ___models_ExampleValue,
)
from ..models import (
    ExampleValueEmpty as ___models_ExampleValueEmpty,
)
from ..models import (
    ExampleValueNumber as ___models_ExampleValueNumber,
)
from ..models import (
    ExampleValueText as ___models_ExampleValueText,
)
from ..models import (
    ExampleValueUnknown as ___models_ExampleValueUnknown,
)
from ..models import (
    PartitionItem000 as ___models_PartitionItem000,
)
from ..models import (
    PartitionItem001 as ___models_PartitionItem001,
)
from ..models import (
    PartitionItem002 as ___models_PartitionItem002,
)
from ..models import (
    PartitionItem003 as ___models_PartitionItem003,
)
from ..models import (
    PartitionItem004 as ___models_PartitionItem004,
)
from ..models import (
    PartitionItem005 as ___models_PartitionItem005,
)
from ..models import (
    PartitionItem006 as ___models_PartitionItem006,
)
from ..models import (
    PartitionItem007 as ___models_PartitionItem007,
)
from ..models import (
    PartitionItem008 as ___models_PartitionItem008,
)
from ..models import (
    PartitionItem009 as ___models_PartitionItem009,
)
from ..models import (
    PartitionItem010 as ___models_PartitionItem010,
)
from ..models import (
    PartitionItem011 as ___models_PartitionItem011,
)
from ..models import (
    PartitionItem012 as ___models_PartitionItem012,
)
from ..models import (
    PartitionItem013 as ___models_PartitionItem013,
)
from ..models import (
    PartitionItem014 as ___models_PartitionItem014,
)
from ..models import (
    PartitionItem015 as ___models_PartitionItem015,
)
from ..models import (
    PartitionItem016 as ___models_PartitionItem016,
)
from ..models import (
    PartitionItem017 as ___models_PartitionItem017,
)
from ..models import (
    PartitionItem018 as ___models_PartitionItem018,
)
from ..models import (
    PartitionItem019 as ___models_PartitionItem019,
)
from ..models import (
    PartitionItem020 as ___models_PartitionItem020,
)
from ..models import (
    PartitionItem021 as ___models_PartitionItem021,
)
from ..models import (
    PartitionItem022 as ___models_PartitionItem022,
)
from ..models import (
    PartitionItem023 as ___models_PartitionItem023,
)
from ..models import (
    PartitionItem024 as ___models_PartitionItem024,
)
from ..models import (
    PartitionItem025 as ___models_PartitionItem025,
)
from ..models import (
    PartitionItem026 as ___models_PartitionItem026,
)
from ..models import (
    PartitionItem027 as ___models_PartitionItem027,
)
from ..models import (
    PartitionItem028 as ___models_PartitionItem028,
)
from ..models import (
    PartitionItem029 as ___models_PartitionItem029,
)
from ..models import (
    PartitionItem030 as ___models_PartitionItem030,
)
from ..models import (
    PartitionItem031 as ___models_PartitionItem031,
)
from ..models import (
    PartitionItem032 as ___models_PartitionItem032,
)
from ..models import (
    PartitionItem033 as ___models_PartitionItem033,
)
from ..models import (
    PartitionItem034 as ___models_PartitionItem034,
)
from ..models import (
    PartitionItem035 as ___models_PartitionItem035,
)
from ..models import (
    PartitionItem036 as ___models_PartitionItem036,
)
from ..models import (
    PartitionItem037 as ___models_PartitionItem037,
)
from ..models import (
    PartitionItem038 as ___models_PartitionItem038,
)
from ..models import (
    PartitionItem039 as ___models_PartitionItem039,
)
from ..models import (
    PartitionItem040 as ___models_PartitionItem040,
)
from ..models import (
    PartitionItem041 as ___models_PartitionItem041,
)
from ..models import (
    PartitionItem042 as ___models_PartitionItem042,
)
from ..models import (
    PartitionItem043 as ___models_PartitionItem043,
)
from ..models import (
    PartitionItem044 as ___models_PartitionItem044,
)
from ..models import (
    PartitionItem045 as ___models_PartitionItem045,
)
from ..models import (
    PartitionItem046 as ___models_PartitionItem046,
)
from ..models import (
    PartitionItem047 as ___models_PartitionItem047,
)
from ..models import (
    PartitionItem048 as ___models_PartitionItem048,
)
from ..models import (
    PartitionItem049 as ___models_PartitionItem049,
)
from ..models import (
    PartitionItem050 as ___models_PartitionItem050,
)
from ..models import (
    PartitionItem051 as ___models_PartitionItem051,
)
from ..models import (
    PartitionItem052 as ___models_PartitionItem052,
)
from ..models import (
    PartitionItem053 as ___models_PartitionItem053,
)
from ..models import (
    PartitionItem054 as ___models_PartitionItem054,
)
from ..models import (
    PartitionItem055 as ___models_PartitionItem055,
)
from ..models import (
    PartitionItem056 as ___models_PartitionItem056,
)
from ..models import (
    PartitionItem057 as ___models_PartitionItem057,
)
from ..models import (
    PartitionItem058 as ___models_PartitionItem058,
)
from ..models import (
    PartitionItem059 as ___models_PartitionItem059,
)
from ..models import (
    PartitionItem060 as ___models_PartitionItem060,
)
from ..models import (
    PartitionItem061 as ___models_PartitionItem061,
)
from ..models import (
    PartitionItem062 as ___models_PartitionItem062,
)
from ..models import (
    PartitionItem063 as ___models_PartitionItem063,
)
from ..models import (
    PartitionItem064 as ___models_PartitionItem064,
)
from ..models import (
    PartitionItem065 as ___models_PartitionItem065,
)
from ..models import (
    PartitionItem066 as ___models_PartitionItem066,
)
from ..models import (
    PartitionItem067 as ___models_PartitionItem067,
)
from ..models import (
    PartitionItem068 as ___models_PartitionItem068,
)
from ..models import (
    PartitionItem069 as ___models_PartitionItem069,
)
from ..models import (
    PartitionItem070 as ___models_PartitionItem070,
)
from ..models import (
    PartitionItem071 as ___models_PartitionItem071,
)
from ..models import (
    PartitionItem072 as ___models_PartitionItem072,
)
from ..models import (
    PartitionItem073 as ___models_PartitionItem073,
)
from ..models import (
    PartitionItem074 as ___models_PartitionItem074,
)
from ..models import (
    PartitionItem075 as ___models_PartitionItem075,
)
from ..models import (
    PartitionItem076 as ___models_PartitionItem076,
)
from ..models import (
    PartitionItem077 as ___models_PartitionItem077,
)
from ..models import (
    PartitionItem078 as ___models_PartitionItem078,
)
from ..models import (
    PartitionItem079 as ___models_PartitionItem079,
)
from ..models import (
    PartitionItem080 as ___models_PartitionItem080,
)
from ..models import (
    PartitionItem081 as ___models_PartitionItem081,
)
from ..models import (
    PartitionItem082 as ___models_PartitionItem082,
)
from ..models import (
    PartitionItem083 as ___models_PartitionItem083,
)
from ..models import (
    PartitionItem084 as ___models_PartitionItem084,
)
from ..models import (
    PartitionItem085 as ___models_PartitionItem085,
)
from ..models import (
    PartitionItem086 as ___models_PartitionItem086,
)
from ..models import (
    PartitionItem087 as ___models_PartitionItem087,
)
from ..models import (
    PartitionItem088 as ___models_PartitionItem088,
)
from ..models import (
    PartitionItem089 as ___models_PartitionItem089,
)
from ..models import (
    PartitionItem090 as ___models_PartitionItem090,
)
from ..models import (
    PartitionItem091 as ___models_PartitionItem091,
)
from ..models import (
    PartitionItem092 as ___models_PartitionItem092,
)
from ..models import (
    PartitionItem093 as ___models_PartitionItem093,
)
from ..models import (
    PartitionItem094 as ___models_PartitionItem094,
)
from ..models import (
    PartitionItem095 as ___models_PartitionItem095,
)
from ..models import (
    PartitionItem096 as ___models_PartitionItem096,
)
from ..models import (
    PartitionItem097 as ___models_PartitionItem097,
)
from ..models import (
    PartitionItem098 as ___models_PartitionItem098,
)
from ..models import (
    PartitionItem099 as ___models_PartitionItem099,
)
from ..models import (
    PartitionItem100 as ___models_PartitionItem100,
)
from ..models import (
    PartitionItem101 as ___models_PartitionItem101,
)
from ..models import (
    PartitionItem102 as ___models_PartitionItem102,
)
from ..models import (
    PartitionItem103 as ___models_PartitionItem103,
)
from ..models import (
    PartitionItem104 as ___models_PartitionItem104,
)
from ..models import (
    PartitionItem105 as ___models_PartitionItem105,
)
from ..models import (
    PartitionItem106 as ___models_PartitionItem106,
)
from ..models import (
    PartitionItem107 as ___models_PartitionItem107,
)
from ..models import (
    PartitionItem108 as ___models_PartitionItem108,
)
from ..models import (
    PartitionItem109 as ___models_PartitionItem109,
)
from ..models import (
    PartitionItem110 as ___models_PartitionItem110,
)
from ..models import (
    PartitionItem111 as ___models_PartitionItem111,
)
from ..models import (
    PartitionItem112 as ___models_PartitionItem112,
)
from ..models import (
    PartitionItem113 as ___models_PartitionItem113,
)
from ..models import (
    PartitionItem114 as ___models_PartitionItem114,
)
from ..models import (
    PartitionItem115 as ___models_PartitionItem115,
)
from ..models import (
    PartitionItem116 as ___models_PartitionItem116,
)
from ..models import (
    PartitionItem117 as ___models_PartitionItem117,
)
from ..models import (
    PartitionItem118 as ___models_PartitionItem118,
)
from ..models import (
    PartitionItem119 as ___models_PartitionItem119,
)
from ..models import (
    PartitionItem120 as ___models_PartitionItem120,
)
from ..models import (
    PartitionItem121 as ___models_PartitionItem121,
)
from ..models import (
    PartitionItem122 as ___models_PartitionItem122,
)
from ..models import (
    PartitionItem123 as ___models_PartitionItem123,
)
from ..models import (
    PartitionItem124 as ___models_PartitionItem124,
)
from ..models import (
    PartitionItem125 as ___models_PartitionItem125,
)
from ..models import (
    PartitionItem126 as ___models_PartitionItem126,
)
from ..models import (
    PartitionItem127 as ___models_PartitionItem127,
)
from ..models import (
    PartitionItem128 as ___models_PartitionItem128,
)
from ..models import (
    PartitionItem129 as ___models_PartitionItem129,
)
from ..models import (
    PartitionItem130 as ___models_PartitionItem130,
)
from ..models import (
    PartitionItem131 as ___models_PartitionItem131,
)
from ..models import (
    PartitionItem132 as ___models_PartitionItem132,
)
from ..models import (
    PartitionItem133 as ___models_PartitionItem133,
)
from ..models import (
    PartitionItem134 as ___models_PartitionItem134,
)
from ..models import (
    PartitionItem135 as ___models_PartitionItem135,
)
from ..models import (
    PartitionItem136 as ___models_PartitionItem136,
)
from ..models import (
    PartitionItem137 as ___models_PartitionItem137,
)
from ..models import (
    PartitionItem138 as ___models_PartitionItem138,
)
from ..models import (
    PartitionItem139 as ___models_PartitionItem139,
)
from ..models import (
    PartitionItem140 as ___models_PartitionItem140,
)
from ..models import (
    PartitionItem141 as ___models_PartitionItem141,
)
from ..models import (
    PartitionItem142 as ___models_PartitionItem142,
)
from ..models import (
    PartitionItem143 as ___models_PartitionItem143,
)
from ..models import (
    PartitionItem144 as ___models_PartitionItem144,
)
from ..models import (
    PartitionItem145 as ___models_PartitionItem145,
)
from ..models import (
    PartitionItem146 as ___models_PartitionItem146,
)
from ..models import (
    PartitionItem147 as ___models_PartitionItem147,
)
from ..models import (
    PartitionItem148 as ___models_PartitionItem148,
)
from ..models import (
    PartitionItem149 as ___models_PartitionItem149,
)
from ..models import (
    PartitionItem150 as ___models_PartitionItem150,
)
from ..models import (
    PartitionItem151 as ___models_PartitionItem151,
)
from ..models import (
    PartitionItem152 as ___models_PartitionItem152,
)
from ..models import (
    PartitionItem153 as ___models_PartitionItem153,
)
from ..models import (
    PartitionItem154 as ___models_PartitionItem154,
)
from ..models import (
    PartitionItem155 as ___models_PartitionItem155,
)
from ..models import (
    PartitionItem156 as ___models_PartitionItem156,
)
from ..models import (
    PartitionItem157 as ___models_PartitionItem157,
)
from ..models import (
    PartitionItem158 as ___models_PartitionItem158,
)
from ..models import (
    PartitionItem159 as ___models_PartitionItem159,
)
from ..models import (
    PartitionItem160 as ___models_PartitionItem160,
)
from ..models import (
    PartitionItem161 as ___models_PartitionItem161,
)
from ..models import (
    PartitionItem162 as ___models_PartitionItem162,
)
from ..models import (
    PartitionItem163 as ___models_PartitionItem163,
)
from ..models import (
    PartitionItem164 as ___models_PartitionItem164,
)
from ..models import (
    PartitionItem165 as ___models_PartitionItem165,
)
from ..models import (
    PartitionItem166 as ___models_PartitionItem166,
)
from ..models import (
    PartitionItem167 as ___models_PartitionItem167,
)
from ..models import (
    PartitionItem168 as ___models_PartitionItem168,
)
from ..models import (
    PartitionItem169 as ___models_PartitionItem169,
)
from ..models import (
    PartitionItem170 as ___models_PartitionItem170,
)
from ..models import (
    PartitionItem171 as ___models_PartitionItem171,
)
from ..models import (
    PartitionItem172 as ___models_PartitionItem172,
)
from ..models import (
    PartitionItem173 as ___models_PartitionItem173,
)
from ..models import (
    PartitionItem174 as ___models_PartitionItem174,
)
from ..models import (
    PartitionItem175 as ___models_PartitionItem175,
)
from ..models import (
    PartitionItem176 as ___models_PartitionItem176,
)
from ..models import (
    PartitionItem177 as ___models_PartitionItem177,
)
from ..models import (
    PartitionItem178 as ___models_PartitionItem178,
)
from ..models import (
    PartitionItem179 as ___models_PartitionItem179,
)
from ..models import (
    PartitionItem180 as ___models_PartitionItem180,
)
from ..models import (
    PartitionItem181 as ___models_PartitionItem181,
)
from ..models import (
    PartitionItem182 as ___models_PartitionItem182,
)
from ..models import (
    PartitionItem183 as ___models_PartitionItem183,
)
from ..models import (
    PartitionItem184 as ___models_PartitionItem184,
)
from ..models import (
    PartitionItem185 as ___models_PartitionItem185,
)
from ..models import (
    PartitionItem186 as ___models_PartitionItem186,
)
from ..models import (
    PartitionItem187 as ___models_PartitionItem187,
)
from ..models import (
    PartitionItem188 as ___models_PartitionItem188,
)
from ..models import (
    PartitionItem189 as ___models_PartitionItem189,
)
from ..models import (
    PartitionItem190 as ___models_PartitionItem190,
)
from ..models import (
    PartitionItem191 as ___models_PartitionItem191,
)
from ..models import (
    PartitionItem192 as ___models_PartitionItem192,
)
from ..models import (
    PartitionItem193 as ___models_PartitionItem193,
)
from ..models import (
    PartitionItem194 as ___models_PartitionItem194,
)
from ..models import (
    PartitionItem195 as ___models_PartitionItem195,
)
from ..models import (
    PartitionItem196 as ___models_PartitionItem196,
)
from ..models import (
    PartitionItem197 as ___models_PartitionItem197,
)
from ..models import (
    PartitionItem198 as ___models_PartitionItem198,
)
from ..models import (
    PartitionItem199 as ___models_PartitionItem199,
)
from ..models import (
    PartitionItem200 as ___models_PartitionItem200,
)
from ..models import (
    PartitionItem201 as ___models_PartitionItem201,
)
from ..models import (
    PartitionItem202 as ___models_PartitionItem202,
)
from ..models import (
    PartitionItem203 as ___models_PartitionItem203,
)
from ..models import (
    PartitionItem204 as ___models_PartitionItem204,
)
from ..models import (
    PartitionItem205 as ___models_PartitionItem205,
)
from ..models import (
    PartitionItem206 as ___models_PartitionItem206,
)
from ..models import (
    PartitionItem207 as ___models_PartitionItem207,
)
from ..models import (
    PartitionItem208 as ___models_PartitionItem208,
)
from ..models import (
    PartitionItem209 as ___models_PartitionItem209,
)
from ..models import (
    PartitionItem210 as ___models_PartitionItem210,
)
from ..models import (
    PartitionItem211 as ___models_PartitionItem211,
)
from ..models import (
    PartitionItem212 as ___models_PartitionItem212,
)
from ..models import (
    PartitionItem213 as ___models_PartitionItem213,
)
from ..models import (
    PartitionItem214 as ___models_PartitionItem214,
)
from ..models import (
    PartitionItem215 as ___models_PartitionItem215,
)
from ..models import (
    PartitionItem216 as ___models_PartitionItem216,
)
from ..models import (
    PartitionItem217 as ___models_PartitionItem217,
)
from ..models import (
    PartitionItem218 as ___models_PartitionItem218,
)
from ..models import (
    PartitionItem219 as ___models_PartitionItem219,
)
from ..models import (
    PartitionItem220 as ___models_PartitionItem220,
)
from ..models import (
    PartitionItem221 as ___models_PartitionItem221,
)
from ..models import (
    PartitionItem222 as ___models_PartitionItem222,
)
from ..models import (
    PartitionItem223 as ___models_PartitionItem223,
)
from ..models import (
    PartitionItem224 as ___models_PartitionItem224,
)
from ..models import (
    PartitionItem225 as ___models_PartitionItem225,
)
from ..models import (
    PartitionItem226 as ___models_PartitionItem226,
)
from ..models import (
    PartitionItem227 as ___models_PartitionItem227,
)
from ..models import (
    PartitionItem228 as ___models_PartitionItem228,
)
from ..models import (
    PartitionItem229 as ___models_PartitionItem229,
)
from ..models import (
    PartitionItem230 as ___models_PartitionItem230,
)
from ..models import (
    PartitionItem231 as ___models_PartitionItem231,
)
from ..models import (
    PartitionItem232 as ___models_PartitionItem232,
)
from ..models import (
    PartitionItem233 as ___models_PartitionItem233,
)
from ..models import (
    PartitionItem234 as ___models_PartitionItem234,
)
from ..models import (
    PartitionItem235 as ___models_PartitionItem235,
)
from ..models import (
    PartitionItem236 as ___models_PartitionItem236,
)
from ..models import (
    PartitionItem237 as ___models_PartitionItem237,
)
from ..models import (
    PartitionItem238 as ___models_PartitionItem238,
)
from ..models import (
    PartitionItem239 as ___models_PartitionItem239,
)
from ..models import (
    PartitionItem240 as ___models_PartitionItem240,
)
from ..models import (
    PartitionItem241 as ___models_PartitionItem241,
)
from ..models import (
    PartitionItem242,
    ServiceError,
    Unit,
    _SerdeShape,  # pyright: ignore[reportPrivateUsage]
)
from ..models import (
    RenamedExample as ___models_RenamedExample,
)

@dataclass(kw_only=True)
class GetExampleInput(_SerdeShape):
    "Input for retrieving an example."

    id: str | None = ...
    partitioned: ___models_PartitionItem000 | None = ...

@dataclass(kw_only=True)
class GetExampleOutput(_SerdeShape):
    "Dataclass for GetExampleOutput structure."

    example: ___models_RenamedExample | None = ...
    value: ___models_ExampleValue | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ExampleError(ServiceError, _SerdeShape):
    "An example modeled error."

    retry_after_seconds: int | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class RenamedExample(_SerdeShape):
    "A representative generated structure."

    name: str
    "The example name."
    count: int | None = ...
    tags: list[str] | None = ...
    attributes: dict[str, Document] | None = ...
    choice: ___models_ExampleValue | None = ...
    status: str | None = ...
    code: int | None = ...

@dataclass
class ExampleValueText(_SerdeShape):
    value: str

@dataclass
class ExampleValueNumber(_SerdeShape):
    value: int

@dataclass
class ExampleValueEmpty(_SerdeShape):
    value: Unit

@dataclass
class ExampleValueUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

ExampleValue = (
    ___models_ExampleValueText
    | ___models_ExampleValueNumber
    | ___models_ExampleValueEmpty
    | ___models_ExampleValueUnknown
)
"A representative generated union."

class _ExampleValueDeserializer:
    def deserialize(
        self, deserializer: ShapeDeserializer
    ) -> ___models_ExampleValue: ...

@dataclass
class EventStreamExample(_SerdeShape):
    value: ___models_RenamedExample

@dataclass
class EventStreamUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

EventStream = ___models_EventStreamExample | ___models_EventStreamUnknown

class _EventStreamDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> ___models_EventStream: ...

class Status(UnknownEnumMixin, StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Code(UnknownEnumMixin, IntEnum):
    OK = 200
    NOT_FOUND = 404

@dataclass(kw_only=True)
class PartitionItem000(_SerdeShape):
    "Dataclass for PartitionItem000 structure."

    value: str | None = ...
    next: ___models_PartitionItem001 | None = ...

@dataclass(kw_only=True)
class PartitionItem001(_SerdeShape):
    "Dataclass for PartitionItem001 structure."

    value: str | None = ...
    next: ___models_PartitionItem002 | None = ...

@dataclass(kw_only=True)
class PartitionItem002(_SerdeShape):
    "Dataclass for PartitionItem002 structure."

    value: str | None = ...
    next: ___models_PartitionItem003 | None = ...

@dataclass(kw_only=True)
class PartitionItem003(_SerdeShape):
    "Dataclass for PartitionItem003 structure."

    value: str | None = ...
    next: ___models_PartitionItem004 | None = ...

@dataclass(kw_only=True)
class PartitionItem004(_SerdeShape):
    "Dataclass for PartitionItem004 structure."

    value: str | None = ...
    next: ___models_PartitionItem005 | None = ...

@dataclass(kw_only=True)
class PartitionItem005(_SerdeShape):
    "Dataclass for PartitionItem005 structure."

    value: str | None = ...
    next: ___models_PartitionItem006 | None = ...

@dataclass(kw_only=True)
class PartitionItem006(_SerdeShape):
    "Dataclass for PartitionItem006 structure."

    value: str | None = ...
    next: ___models_PartitionItem007 | None = ...

@dataclass(kw_only=True)
class PartitionItem007(_SerdeShape):
    "Dataclass for PartitionItem007 structure."

    value: str | None = ...
    next: ___models_PartitionItem008 | None = ...

@dataclass(kw_only=True)
class PartitionItem008(_SerdeShape):
    "Dataclass for PartitionItem008 structure."

    value: str | None = ...
    next: ___models_PartitionItem009 | None = ...

@dataclass(kw_only=True)
class PartitionItem009(_SerdeShape):
    "Dataclass for PartitionItem009 structure."

    value: str | None = ...
    next: ___models_PartitionItem010 | None = ...

@dataclass(kw_only=True)
class PartitionItem010(_SerdeShape):
    "Dataclass for PartitionItem010 structure."

    value: str | None = ...
    next: ___models_PartitionItem011 | None = ...

@dataclass(kw_only=True)
class PartitionItem011(_SerdeShape):
    "Dataclass for PartitionItem011 structure."

    value: str | None = ...
    next: ___models_PartitionItem012 | None = ...

@dataclass(kw_only=True)
class PartitionItem012(_SerdeShape):
    "Dataclass for PartitionItem012 structure."

    value: str | None = ...
    next: ___models_PartitionItem013 | None = ...

@dataclass(kw_only=True)
class PartitionItem013(_SerdeShape):
    "Dataclass for PartitionItem013 structure."

    value: str | None = ...
    next: ___models_PartitionItem014 | None = ...

@dataclass(kw_only=True)
class PartitionItem014(_SerdeShape):
    "Dataclass for PartitionItem014 structure."

    value: str | None = ...
    next: ___models_PartitionItem015 | None = ...

@dataclass(kw_only=True)
class PartitionItem015(_SerdeShape):
    "Dataclass for PartitionItem015 structure."

    value: str | None = ...
    next: ___models_PartitionItem016 | None = ...

@dataclass(kw_only=True)
class PartitionItem016(_SerdeShape):
    "Dataclass for PartitionItem016 structure."

    value: str | None = ...
    next: ___models_PartitionItem017 | None = ...

@dataclass(kw_only=True)
class PartitionItem017(_SerdeShape):
    "Dataclass for PartitionItem017 structure."

    value: str | None = ...
    next: ___models_PartitionItem018 | None = ...

@dataclass(kw_only=True)
class PartitionItem018(_SerdeShape):
    "Dataclass for PartitionItem018 structure."

    value: str | None = ...
    next: ___models_PartitionItem019 | None = ...

@dataclass(kw_only=True)
class PartitionItem019(_SerdeShape):
    "Dataclass for PartitionItem019 structure."

    value: str | None = ...
    next: ___models_PartitionItem020 | None = ...

@dataclass(kw_only=True)
class PartitionItem020(_SerdeShape):
    "Dataclass for PartitionItem020 structure."

    value: str | None = ...
    next: ___models_PartitionItem021 | None = ...

@dataclass(kw_only=True)
class PartitionItem021(_SerdeShape):
    "Dataclass for PartitionItem021 structure."

    value: str | None = ...
    next: ___models_PartitionItem022 | None = ...

@dataclass(kw_only=True)
class PartitionItem022(_SerdeShape):
    "Dataclass for PartitionItem022 structure."

    value: str | None = ...
    next: ___models_PartitionItem023 | None = ...

@dataclass(kw_only=True)
class PartitionItem023(_SerdeShape):
    "Dataclass for PartitionItem023 structure."

    value: str | None = ...
    next: ___models_PartitionItem024 | None = ...

@dataclass(kw_only=True)
class PartitionItem024(_SerdeShape):
    "Dataclass for PartitionItem024 structure."

    value: str | None = ...
    next: ___models_PartitionItem025 | None = ...

@dataclass(kw_only=True)
class PartitionItem025(_SerdeShape):
    "Dataclass for PartitionItem025 structure."

    value: str | None = ...
    next: ___models_PartitionItem026 | None = ...

@dataclass(kw_only=True)
class PartitionItem026(_SerdeShape):
    "Dataclass for PartitionItem026 structure."

    value: str | None = ...
    next: ___models_PartitionItem027 | None = ...

@dataclass(kw_only=True)
class PartitionItem027(_SerdeShape):
    "Dataclass for PartitionItem027 structure."

    value: str | None = ...
    next: ___models_PartitionItem028 | None = ...

@dataclass(kw_only=True)
class PartitionItem028(_SerdeShape):
    "Dataclass for PartitionItem028 structure."

    value: str | None = ...
    next: ___models_PartitionItem029 | None = ...

@dataclass(kw_only=True)
class PartitionItem029(_SerdeShape):
    "Dataclass for PartitionItem029 structure."

    value: str | None = ...
    next: ___models_PartitionItem030 | None = ...

@dataclass(kw_only=True)
class PartitionItem030(_SerdeShape):
    "Dataclass for PartitionItem030 structure."

    value: str | None = ...
    next: ___models_PartitionItem031 | None = ...

@dataclass(kw_only=True)
class PartitionItem031(_SerdeShape):
    "Dataclass for PartitionItem031 structure."

    value: str | None = ...
    next: ___models_PartitionItem032 | None = ...

@dataclass(kw_only=True)
class PartitionItem032(_SerdeShape):
    "Dataclass for PartitionItem032 structure."

    value: str | None = ...
    next: ___models_PartitionItem033 | None = ...

@dataclass(kw_only=True)
class PartitionItem033(_SerdeShape):
    "Dataclass for PartitionItem033 structure."

    value: str | None = ...
    next: ___models_PartitionItem034 | None = ...

@dataclass(kw_only=True)
class PartitionItem034(_SerdeShape):
    "Dataclass for PartitionItem034 structure."

    value: str | None = ...
    next: ___models_PartitionItem035 | None = ...

@dataclass(kw_only=True)
class PartitionItem035(_SerdeShape):
    "Dataclass for PartitionItem035 structure."

    value: str | None = ...
    next: ___models_PartitionItem036 | None = ...

@dataclass(kw_only=True)
class PartitionItem036(_SerdeShape):
    "Dataclass for PartitionItem036 structure."

    value: str | None = ...
    next: ___models_PartitionItem037 | None = ...

@dataclass(kw_only=True)
class PartitionItem037(_SerdeShape):
    "Dataclass for PartitionItem037 structure."

    value: str | None = ...
    next: ___models_PartitionItem038 | None = ...

@dataclass(kw_only=True)
class PartitionItem038(_SerdeShape):
    "Dataclass for PartitionItem038 structure."

    value: str | None = ...
    next: ___models_PartitionItem039 | None = ...

@dataclass(kw_only=True)
class PartitionItem039(_SerdeShape):
    "Dataclass for PartitionItem039 structure."

    value: str | None = ...
    next: ___models_PartitionItem040 | None = ...

@dataclass(kw_only=True)
class PartitionItem040(_SerdeShape):
    "Dataclass for PartitionItem040 structure."

    value: str | None = ...
    next: ___models_PartitionItem041 | None = ...

@dataclass(kw_only=True)
class PartitionItem041(_SerdeShape):
    "Dataclass for PartitionItem041 structure."

    value: str | None = ...
    next: ___models_PartitionItem042 | None = ...

@dataclass(kw_only=True)
class PartitionItem042(_SerdeShape):
    "Dataclass for PartitionItem042 structure."

    value: str | None = ...
    next: ___models_PartitionItem043 | None = ...

@dataclass(kw_only=True)
class PartitionItem043(_SerdeShape):
    "Dataclass for PartitionItem043 structure."

    value: str | None = ...
    next: ___models_PartitionItem044 | None = ...

@dataclass(kw_only=True)
class PartitionItem044(_SerdeShape):
    "Dataclass for PartitionItem044 structure."

    value: str | None = ...
    next: ___models_PartitionItem045 | None = ...

@dataclass(kw_only=True)
class PartitionItem045(_SerdeShape):
    "Dataclass for PartitionItem045 structure."

    value: str | None = ...
    next: ___models_PartitionItem046 | None = ...

@dataclass(kw_only=True)
class PartitionItem046(_SerdeShape):
    "Dataclass for PartitionItem046 structure."

    value: str | None = ...
    next: ___models_PartitionItem047 | None = ...

@dataclass(kw_only=True)
class PartitionItem047(_SerdeShape):
    "Dataclass for PartitionItem047 structure."

    value: str | None = ...
    next: ___models_PartitionItem048 | None = ...

@dataclass(kw_only=True)
class PartitionItem048(_SerdeShape):
    "Dataclass for PartitionItem048 structure."

    value: str | None = ...
    next: ___models_PartitionItem049 | None = ...

@dataclass(kw_only=True)
class PartitionItem049(_SerdeShape):
    "Dataclass for PartitionItem049 structure."

    value: str | None = ...
    next: ___models_PartitionItem050 | None = ...

@dataclass(kw_only=True)
class PartitionItem050(_SerdeShape):
    "Dataclass for PartitionItem050 structure."

    value: str | None = ...
    next: ___models_PartitionItem051 | None = ...

@dataclass(kw_only=True)
class PartitionItem051(_SerdeShape):
    "Dataclass for PartitionItem051 structure."

    value: str | None = ...
    next: ___models_PartitionItem052 | None = ...

@dataclass(kw_only=True)
class PartitionItem052(_SerdeShape):
    "Dataclass for PartitionItem052 structure."

    value: str | None = ...
    next: ___models_PartitionItem053 | None = ...

@dataclass(kw_only=True)
class PartitionItem053(_SerdeShape):
    "Dataclass for PartitionItem053 structure."

    value: str | None = ...
    next: ___models_PartitionItem054 | None = ...

@dataclass(kw_only=True)
class PartitionItem054(_SerdeShape):
    "Dataclass for PartitionItem054 structure."

    value: str | None = ...
    next: ___models_PartitionItem055 | None = ...

@dataclass(kw_only=True)
class PartitionItem055(_SerdeShape):
    "Dataclass for PartitionItem055 structure."

    value: str | None = ...
    next: ___models_PartitionItem056 | None = ...

@dataclass(kw_only=True)
class PartitionItem056(_SerdeShape):
    "Dataclass for PartitionItem056 structure."

    value: str | None = ...
    next: ___models_PartitionItem057 | None = ...

@dataclass(kw_only=True)
class PartitionItem057(_SerdeShape):
    "Dataclass for PartitionItem057 structure."

    value: str | None = ...
    next: ___models_PartitionItem058 | None = ...

@dataclass(kw_only=True)
class PartitionItem058(_SerdeShape):
    "Dataclass for PartitionItem058 structure."

    value: str | None = ...
    next: ___models_PartitionItem059 | None = ...

@dataclass(kw_only=True)
class PartitionItem059(_SerdeShape):
    "Dataclass for PartitionItem059 structure."

    value: str | None = ...
    next: ___models_PartitionItem060 | None = ...

@dataclass(kw_only=True)
class PartitionItem060(_SerdeShape):
    "Dataclass for PartitionItem060 structure."

    value: str | None = ...
    next: ___models_PartitionItem061 | None = ...

@dataclass(kw_only=True)
class PartitionItem061(_SerdeShape):
    "Dataclass for PartitionItem061 structure."

    value: str | None = ...
    next: ___models_PartitionItem062 | None = ...

@dataclass(kw_only=True)
class PartitionItem062(_SerdeShape):
    "Dataclass for PartitionItem062 structure."

    value: str | None = ...
    next: ___models_PartitionItem063 | None = ...

@dataclass(kw_only=True)
class PartitionItem063(_SerdeShape):
    "Dataclass for PartitionItem063 structure."

    value: str | None = ...
    next: ___models_PartitionItem064 | None = ...

@dataclass(kw_only=True)
class PartitionItem064(_SerdeShape):
    "Dataclass for PartitionItem064 structure."

    value: str | None = ...
    next: ___models_PartitionItem065 | None = ...

@dataclass(kw_only=True)
class PartitionItem065(_SerdeShape):
    "Dataclass for PartitionItem065 structure."

    value: str | None = ...
    next: ___models_PartitionItem066 | None = ...

@dataclass(kw_only=True)
class PartitionItem066(_SerdeShape):
    "Dataclass for PartitionItem066 structure."

    value: str | None = ...
    next: ___models_PartitionItem067 | None = ...

@dataclass(kw_only=True)
class PartitionItem067(_SerdeShape):
    "Dataclass for PartitionItem067 structure."

    value: str | None = ...
    next: ___models_PartitionItem068 | None = ...

@dataclass(kw_only=True)
class PartitionItem068(_SerdeShape):
    "Dataclass for PartitionItem068 structure."

    value: str | None = ...
    next: ___models_PartitionItem069 | None = ...

@dataclass(kw_only=True)
class PartitionItem069(_SerdeShape):
    "Dataclass for PartitionItem069 structure."

    value: str | None = ...
    next: ___models_PartitionItem070 | None = ...

@dataclass(kw_only=True)
class PartitionItem070(_SerdeShape):
    "Dataclass for PartitionItem070 structure."

    value: str | None = ...
    next: ___models_PartitionItem071 | None = ...

@dataclass(kw_only=True)
class PartitionItem071(_SerdeShape):
    "Dataclass for PartitionItem071 structure."

    value: str | None = ...
    next: ___models_PartitionItem072 | None = ...

@dataclass(kw_only=True)
class PartitionItem072(_SerdeShape):
    "Dataclass for PartitionItem072 structure."

    value: str | None = ...
    next: ___models_PartitionItem073 | None = ...

@dataclass(kw_only=True)
class PartitionItem073(_SerdeShape):
    "Dataclass for PartitionItem073 structure."

    value: str | None = ...
    next: ___models_PartitionItem074 | None = ...

@dataclass(kw_only=True)
class PartitionItem074(_SerdeShape):
    "Dataclass for PartitionItem074 structure."

    value: str | None = ...
    next: ___models_PartitionItem075 | None = ...

@dataclass(kw_only=True)
class PartitionItem075(_SerdeShape):
    "Dataclass for PartitionItem075 structure."

    value: str | None = ...
    next: ___models_PartitionItem076 | None = ...

@dataclass(kw_only=True)
class PartitionItem076(_SerdeShape):
    "Dataclass for PartitionItem076 structure."

    value: str | None = ...
    next: ___models_PartitionItem077 | None = ...

@dataclass(kw_only=True)
class PartitionItem077(_SerdeShape):
    "Dataclass for PartitionItem077 structure."

    value: str | None = ...
    next: ___models_PartitionItem078 | None = ...

@dataclass(kw_only=True)
class PartitionItem078(_SerdeShape):
    "Dataclass for PartitionItem078 structure."

    value: str | None = ...
    next: ___models_PartitionItem079 | None = ...

@dataclass(kw_only=True)
class PartitionItem079(_SerdeShape):
    "Dataclass for PartitionItem079 structure."

    value: str | None = ...
    next: ___models_PartitionItem080 | None = ...

@dataclass(kw_only=True)
class PartitionItem080(_SerdeShape):
    "Dataclass for PartitionItem080 structure."

    value: str | None = ...
    next: ___models_PartitionItem081 | None = ...

@dataclass(kw_only=True)
class PartitionItem081(_SerdeShape):
    "Dataclass for PartitionItem081 structure."

    value: str | None = ...
    next: ___models_PartitionItem082 | None = ...

@dataclass(kw_only=True)
class PartitionItem082(_SerdeShape):
    "Dataclass for PartitionItem082 structure."

    value: str | None = ...
    next: ___models_PartitionItem083 | None = ...

@dataclass(kw_only=True)
class PartitionItem083(_SerdeShape):
    "Dataclass for PartitionItem083 structure."

    value: str | None = ...
    next: ___models_PartitionItem084 | None = ...

@dataclass(kw_only=True)
class PartitionItem084(_SerdeShape):
    "Dataclass for PartitionItem084 structure."

    value: str | None = ...
    next: ___models_PartitionItem085 | None = ...

@dataclass(kw_only=True)
class PartitionItem085(_SerdeShape):
    "Dataclass for PartitionItem085 structure."

    value: str | None = ...
    next: ___models_PartitionItem086 | None = ...

@dataclass(kw_only=True)
class PartitionItem086(_SerdeShape):
    "Dataclass for PartitionItem086 structure."

    value: str | None = ...
    next: ___models_PartitionItem087 | None = ...

@dataclass(kw_only=True)
class PartitionItem087(_SerdeShape):
    "Dataclass for PartitionItem087 structure."

    value: str | None = ...
    next: ___models_PartitionItem088 | None = ...

@dataclass(kw_only=True)
class PartitionItem088(_SerdeShape):
    "Dataclass for PartitionItem088 structure."

    value: str | None = ...
    next: ___models_PartitionItem089 | None = ...

@dataclass(kw_only=True)
class PartitionItem089(_SerdeShape):
    "Dataclass for PartitionItem089 structure."

    value: str | None = ...
    next: ___models_PartitionItem090 | None = ...

@dataclass(kw_only=True)
class PartitionItem090(_SerdeShape):
    "Dataclass for PartitionItem090 structure."

    value: str | None = ...
    next: ___models_PartitionItem091 | None = ...

@dataclass(kw_only=True)
class PartitionItem091(_SerdeShape):
    "Dataclass for PartitionItem091 structure."

    value: str | None = ...
    next: ___models_PartitionItem092 | None = ...

@dataclass(kw_only=True)
class PartitionItem092(_SerdeShape):
    "Dataclass for PartitionItem092 structure."

    value: str | None = ...
    next: ___models_PartitionItem093 | None = ...

@dataclass(kw_only=True)
class PartitionItem093(_SerdeShape):
    "Dataclass for PartitionItem093 structure."

    value: str | None = ...
    next: ___models_PartitionItem094 | None = ...

@dataclass(kw_only=True)
class PartitionItem094(_SerdeShape):
    "Dataclass for PartitionItem094 structure."

    value: str | None = ...
    next: ___models_PartitionItem095 | None = ...

@dataclass(kw_only=True)
class PartitionItem095(_SerdeShape):
    "Dataclass for PartitionItem095 structure."

    value: str | None = ...
    next: ___models_PartitionItem096 | None = ...

@dataclass(kw_only=True)
class PartitionItem096(_SerdeShape):
    "Dataclass for PartitionItem096 structure."

    value: str | None = ...
    next: ___models_PartitionItem097 | None = ...

@dataclass(kw_only=True)
class PartitionItem097(_SerdeShape):
    "Dataclass for PartitionItem097 structure."

    value: str | None = ...
    next: ___models_PartitionItem098 | None = ...

@dataclass(kw_only=True)
class PartitionItem098(_SerdeShape):
    "Dataclass for PartitionItem098 structure."

    value: str | None = ...
    next: ___models_PartitionItem099 | None = ...

@dataclass(kw_only=True)
class PartitionItem099(_SerdeShape):
    "Dataclass for PartitionItem099 structure."

    value: str | None = ...
    next: ___models_PartitionItem100 | None = ...

@dataclass(kw_only=True)
class PartitionItem100(_SerdeShape):
    "Dataclass for PartitionItem100 structure."

    value: str | None = ...
    next: ___models_PartitionItem101 | None = ...

@dataclass(kw_only=True)
class PartitionItem101(_SerdeShape):
    "Dataclass for PartitionItem101 structure."

    value: str | None = ...
    next: ___models_PartitionItem102 | None = ...

@dataclass(kw_only=True)
class PartitionItem102(_SerdeShape):
    "Dataclass for PartitionItem102 structure."

    value: str | None = ...
    next: ___models_PartitionItem103 | None = ...

@dataclass(kw_only=True)
class PartitionItem103(_SerdeShape):
    "Dataclass for PartitionItem103 structure."

    value: str | None = ...
    next: ___models_PartitionItem104 | None = ...

@dataclass(kw_only=True)
class PartitionItem104(_SerdeShape):
    "Dataclass for PartitionItem104 structure."

    value: str | None = ...
    next: ___models_PartitionItem105 | None = ...

@dataclass(kw_only=True)
class PartitionItem105(_SerdeShape):
    "Dataclass for PartitionItem105 structure."

    value: str | None = ...
    next: ___models_PartitionItem106 | None = ...

@dataclass(kw_only=True)
class PartitionItem106(_SerdeShape):
    "Dataclass for PartitionItem106 structure."

    value: str | None = ...
    next: ___models_PartitionItem107 | None = ...

@dataclass(kw_only=True)
class PartitionItem107(_SerdeShape):
    "Dataclass for PartitionItem107 structure."

    value: str | None = ...
    next: ___models_PartitionItem108 | None = ...

@dataclass(kw_only=True)
class PartitionItem108(_SerdeShape):
    "Dataclass for PartitionItem108 structure."

    value: str | None = ...
    next: ___models_PartitionItem109 | None = ...

@dataclass(kw_only=True)
class PartitionItem109(_SerdeShape):
    "Dataclass for PartitionItem109 structure."

    value: str | None = ...
    next: ___models_PartitionItem110 | None = ...

@dataclass(kw_only=True)
class PartitionItem110(_SerdeShape):
    "Dataclass for PartitionItem110 structure."

    value: str | None = ...
    next: ___models_PartitionItem111 | None = ...

@dataclass(kw_only=True)
class PartitionItem111(_SerdeShape):
    "Dataclass for PartitionItem111 structure."

    value: str | None = ...
    next: ___models_PartitionItem112 | None = ...

@dataclass(kw_only=True)
class PartitionItem112(_SerdeShape):
    "Dataclass for PartitionItem112 structure."

    value: str | None = ...
    next: ___models_PartitionItem113 | None = ...

@dataclass(kw_only=True)
class PartitionItem113(_SerdeShape):
    "Dataclass for PartitionItem113 structure."

    value: str | None = ...
    next: ___models_PartitionItem114 | None = ...

@dataclass(kw_only=True)
class PartitionItem114(_SerdeShape):
    "Dataclass for PartitionItem114 structure."

    value: str | None = ...
    next: ___models_PartitionItem115 | None = ...

@dataclass(kw_only=True)
class PartitionItem115(_SerdeShape):
    "Dataclass for PartitionItem115 structure."

    value: str | None = ...
    next: ___models_PartitionItem116 | None = ...

@dataclass(kw_only=True)
class PartitionItem116(_SerdeShape):
    "Dataclass for PartitionItem116 structure."

    value: str | None = ...
    next: ___models_PartitionItem117 | None = ...

@dataclass(kw_only=True)
class PartitionItem117(_SerdeShape):
    "Dataclass for PartitionItem117 structure."

    value: str | None = ...
    next: ___models_PartitionItem118 | None = ...

@dataclass(kw_only=True)
class PartitionItem118(_SerdeShape):
    "Dataclass for PartitionItem118 structure."

    value: str | None = ...
    next: ___models_PartitionItem119 | None = ...

@dataclass(kw_only=True)
class PartitionItem119(_SerdeShape):
    "Dataclass for PartitionItem119 structure."

    value: str | None = ...
    next: ___models_PartitionItem120 | None = ...

@dataclass(kw_only=True)
class PartitionItem120(_SerdeShape):
    "Dataclass for PartitionItem120 structure."

    value: str | None = ...
    next: ___models_PartitionItem121 | None = ...

@dataclass(kw_only=True)
class PartitionItem121(_SerdeShape):
    "Dataclass for PartitionItem121 structure."

    value: str | None = ...
    next: ___models_PartitionItem122 | None = ...

@dataclass(kw_only=True)
class PartitionItem122(_SerdeShape):
    "Dataclass for PartitionItem122 structure."

    value: str | None = ...
    next: ___models_PartitionItem123 | None = ...

@dataclass(kw_only=True)
class PartitionItem123(_SerdeShape):
    "Dataclass for PartitionItem123 structure."

    value: str | None = ...
    next: ___models_PartitionItem124 | None = ...

@dataclass(kw_only=True)
class PartitionItem124(_SerdeShape):
    "Dataclass for PartitionItem124 structure."

    value: str | None = ...
    next: ___models_PartitionItem125 | None = ...

@dataclass(kw_only=True)
class PartitionItem125(_SerdeShape):
    "Dataclass for PartitionItem125 structure."

    value: str | None = ...
    next: ___models_PartitionItem126 | None = ...

@dataclass(kw_only=True)
class PartitionItem126(_SerdeShape):
    "Dataclass for PartitionItem126 structure."

    value: str | None = ...
    next: ___models_PartitionItem127 | None = ...

@dataclass(kw_only=True)
class PartitionItem127(_SerdeShape):
    "Dataclass for PartitionItem127 structure."

    value: str | None = ...
    next: ___models_PartitionItem128 | None = ...

@dataclass(kw_only=True)
class PartitionItem128(_SerdeShape):
    "Dataclass for PartitionItem128 structure."

    value: str | None = ...
    next: ___models_PartitionItem129 | None = ...

@dataclass(kw_only=True)
class PartitionItem129(_SerdeShape):
    "Dataclass for PartitionItem129 structure."

    value: str | None = ...
    next: ___models_PartitionItem130 | None = ...

@dataclass(kw_only=True)
class PartitionItem130(_SerdeShape):
    "Dataclass for PartitionItem130 structure."

    value: str | None = ...
    next: ___models_PartitionItem131 | None = ...

@dataclass(kw_only=True)
class PartitionItem131(_SerdeShape):
    "Dataclass for PartitionItem131 structure."

    value: str | None = ...
    next: ___models_PartitionItem132 | None = ...

@dataclass(kw_only=True)
class PartitionItem132(_SerdeShape):
    "Dataclass for PartitionItem132 structure."

    value: str | None = ...
    next: ___models_PartitionItem133 | None = ...

@dataclass(kw_only=True)
class PartitionItem133(_SerdeShape):
    "Dataclass for PartitionItem133 structure."

    value: str | None = ...
    next: ___models_PartitionItem134 | None = ...

@dataclass(kw_only=True)
class PartitionItem134(_SerdeShape):
    "Dataclass for PartitionItem134 structure."

    value: str | None = ...
    next: ___models_PartitionItem135 | None = ...

@dataclass(kw_only=True)
class PartitionItem135(_SerdeShape):
    "Dataclass for PartitionItem135 structure."

    value: str | None = ...
    next: ___models_PartitionItem136 | None = ...

@dataclass(kw_only=True)
class PartitionItem136(_SerdeShape):
    "Dataclass for PartitionItem136 structure."

    value: str | None = ...
    next: ___models_PartitionItem137 | None = ...

@dataclass(kw_only=True)
class PartitionItem137(_SerdeShape):
    "Dataclass for PartitionItem137 structure."

    value: str | None = ...
    next: ___models_PartitionItem138 | None = ...

@dataclass(kw_only=True)
class PartitionItem138(_SerdeShape):
    "Dataclass for PartitionItem138 structure."

    value: str | None = ...
    next: ___models_PartitionItem139 | None = ...

@dataclass(kw_only=True)
class PartitionItem139(_SerdeShape):
    "Dataclass for PartitionItem139 structure."

    value: str | None = ...
    next: ___models_PartitionItem140 | None = ...

@dataclass(kw_only=True)
class PartitionItem140(_SerdeShape):
    "Dataclass for PartitionItem140 structure."

    value: str | None = ...
    next: ___models_PartitionItem141 | None = ...

@dataclass(kw_only=True)
class PartitionItem141(_SerdeShape):
    "Dataclass for PartitionItem141 structure."

    value: str | None = ...
    next: ___models_PartitionItem142 | None = ...

@dataclass(kw_only=True)
class PartitionItem142(_SerdeShape):
    "Dataclass for PartitionItem142 structure."

    value: str | None = ...
    next: ___models_PartitionItem143 | None = ...

@dataclass(kw_only=True)
class PartitionItem143(_SerdeShape):
    "Dataclass for PartitionItem143 structure."

    value: str | None = ...
    next: ___models_PartitionItem144 | None = ...

@dataclass(kw_only=True)
class PartitionItem144(_SerdeShape):
    "Dataclass for PartitionItem144 structure."

    value: str | None = ...
    next: ___models_PartitionItem145 | None = ...

@dataclass(kw_only=True)
class PartitionItem145(_SerdeShape):
    "Dataclass for PartitionItem145 structure."

    value: str | None = ...
    next: ___models_PartitionItem146 | None = ...

@dataclass(kw_only=True)
class PartitionItem146(_SerdeShape):
    "Dataclass for PartitionItem146 structure."

    value: str | None = ...
    next: ___models_PartitionItem147 | None = ...

@dataclass(kw_only=True)
class PartitionItem147(_SerdeShape):
    "Dataclass for PartitionItem147 structure."

    value: str | None = ...
    next: ___models_PartitionItem148 | None = ...

@dataclass(kw_only=True)
class PartitionItem148(_SerdeShape):
    "Dataclass for PartitionItem148 structure."

    value: str | None = ...
    next: ___models_PartitionItem149 | None = ...

@dataclass(kw_only=True)
class PartitionItem149(_SerdeShape):
    "Dataclass for PartitionItem149 structure."

    value: str | None = ...
    next: ___models_PartitionItem150 | None = ...

@dataclass(kw_only=True)
class PartitionItem150(_SerdeShape):
    "Dataclass for PartitionItem150 structure."

    value: str | None = ...
    next: ___models_PartitionItem151 | None = ...

@dataclass(kw_only=True)
class PartitionItem151(_SerdeShape):
    "Dataclass for PartitionItem151 structure."

    value: str | None = ...
    next: ___models_PartitionItem152 | None = ...

@dataclass(kw_only=True)
class PartitionItem152(_SerdeShape):
    "Dataclass for PartitionItem152 structure."

    value: str | None = ...
    next: ___models_PartitionItem153 | None = ...

@dataclass(kw_only=True)
class PartitionItem153(_SerdeShape):
    "Dataclass for PartitionItem153 structure."

    value: str | None = ...
    next: ___models_PartitionItem154 | None = ...

@dataclass(kw_only=True)
class PartitionItem154(_SerdeShape):
    "Dataclass for PartitionItem154 structure."

    value: str | None = ...
    next: ___models_PartitionItem155 | None = ...

@dataclass(kw_only=True)
class PartitionItem155(_SerdeShape):
    "Dataclass for PartitionItem155 structure."

    value: str | None = ...
    next: ___models_PartitionItem156 | None = ...

@dataclass(kw_only=True)
class PartitionItem156(_SerdeShape):
    "Dataclass for PartitionItem156 structure."

    value: str | None = ...
    next: ___models_PartitionItem157 | None = ...

@dataclass(kw_only=True)
class PartitionItem157(_SerdeShape):
    "Dataclass for PartitionItem157 structure."

    value: str | None = ...
    next: ___models_PartitionItem158 | None = ...

@dataclass(kw_only=True)
class PartitionItem158(_SerdeShape):
    "Dataclass for PartitionItem158 structure."

    value: str | None = ...
    next: ___models_PartitionItem159 | None = ...

@dataclass(kw_only=True)
class PartitionItem159(_SerdeShape):
    "Dataclass for PartitionItem159 structure."

    value: str | None = ...
    next: ___models_PartitionItem160 | None = ...

@dataclass(kw_only=True)
class PartitionItem160(_SerdeShape):
    "Dataclass for PartitionItem160 structure."

    value: str | None = ...
    next: ___models_PartitionItem161 | None = ...

@dataclass(kw_only=True)
class PartitionItem161(_SerdeShape):
    "Dataclass for PartitionItem161 structure."

    value: str | None = ...
    next: ___models_PartitionItem162 | None = ...

@dataclass(kw_only=True)
class PartitionItem162(_SerdeShape):
    "Dataclass for PartitionItem162 structure."

    value: str | None = ...
    next: ___models_PartitionItem163 | None = ...

@dataclass(kw_only=True)
class PartitionItem163(_SerdeShape):
    "Dataclass for PartitionItem163 structure."

    value: str | None = ...
    next: ___models_PartitionItem164 | None = ...

@dataclass(kw_only=True)
class PartitionItem164(_SerdeShape):
    "Dataclass for PartitionItem164 structure."

    value: str | None = ...
    next: ___models_PartitionItem165 | None = ...

@dataclass(kw_only=True)
class PartitionItem165(_SerdeShape):
    "Dataclass for PartitionItem165 structure."

    value: str | None = ...
    next: ___models_PartitionItem166 | None = ...

@dataclass(kw_only=True)
class PartitionItem166(_SerdeShape):
    "Dataclass for PartitionItem166 structure."

    value: str | None = ...
    next: ___models_PartitionItem167 | None = ...

@dataclass(kw_only=True)
class PartitionItem167(_SerdeShape):
    "Dataclass for PartitionItem167 structure."

    value: str | None = ...
    next: ___models_PartitionItem168 | None = ...

@dataclass(kw_only=True)
class PartitionItem168(_SerdeShape):
    "Dataclass for PartitionItem168 structure."

    value: str | None = ...
    next: ___models_PartitionItem169 | None = ...

@dataclass(kw_only=True)
class PartitionItem169(_SerdeShape):
    "Dataclass for PartitionItem169 structure."

    value: str | None = ...
    next: ___models_PartitionItem170 | None = ...

@dataclass(kw_only=True)
class PartitionItem170(_SerdeShape):
    "Dataclass for PartitionItem170 structure."

    value: str | None = ...
    next: ___models_PartitionItem171 | None = ...

@dataclass(kw_only=True)
class PartitionItem171(_SerdeShape):
    "Dataclass for PartitionItem171 structure."

    value: str | None = ...
    next: ___models_PartitionItem172 | None = ...

@dataclass(kw_only=True)
class PartitionItem172(_SerdeShape):
    "Dataclass for PartitionItem172 structure."

    value: str | None = ...
    next: ___models_PartitionItem173 | None = ...

@dataclass(kw_only=True)
class PartitionItem173(_SerdeShape):
    "Dataclass for PartitionItem173 structure."

    value: str | None = ...
    next: ___models_PartitionItem174 | None = ...

@dataclass(kw_only=True)
class PartitionItem174(_SerdeShape):
    "Dataclass for PartitionItem174 structure."

    value: str | None = ...
    next: ___models_PartitionItem175 | None = ...

@dataclass(kw_only=True)
class PartitionItem175(_SerdeShape):
    "Dataclass for PartitionItem175 structure."

    value: str | None = ...
    next: ___models_PartitionItem176 | None = ...

@dataclass(kw_only=True)
class PartitionItem176(_SerdeShape):
    "Dataclass for PartitionItem176 structure."

    value: str | None = ...
    next: ___models_PartitionItem177 | None = ...

@dataclass(kw_only=True)
class PartitionItem177(_SerdeShape):
    "Dataclass for PartitionItem177 structure."

    value: str | None = ...
    next: ___models_PartitionItem178 | None = ...

@dataclass(kw_only=True)
class PartitionItem178(_SerdeShape):
    "Dataclass for PartitionItem178 structure."

    value: str | None = ...
    next: ___models_PartitionItem179 | None = ...

@dataclass(kw_only=True)
class PartitionItem179(_SerdeShape):
    "Dataclass for PartitionItem179 structure."

    value: str | None = ...
    next: ___models_PartitionItem180 | None = ...

@dataclass(kw_only=True)
class PartitionItem180(_SerdeShape):
    "Dataclass for PartitionItem180 structure."

    value: str | None = ...
    next: ___models_PartitionItem181 | None = ...

@dataclass(kw_only=True)
class PartitionItem181(_SerdeShape):
    "Dataclass for PartitionItem181 structure."

    value: str | None = ...
    next: ___models_PartitionItem182 | None = ...

@dataclass(kw_only=True)
class PartitionItem182(_SerdeShape):
    "Dataclass for PartitionItem182 structure."

    value: str | None = ...
    next: ___models_PartitionItem183 | None = ...

@dataclass(kw_only=True)
class PartitionItem183(_SerdeShape):
    "Dataclass for PartitionItem183 structure."

    value: str | None = ...
    next: ___models_PartitionItem184 | None = ...

@dataclass(kw_only=True)
class PartitionItem184(_SerdeShape):
    "Dataclass for PartitionItem184 structure."

    value: str | None = ...
    next: ___models_PartitionItem185 | None = ...

@dataclass(kw_only=True)
class PartitionItem185(_SerdeShape):
    "Dataclass for PartitionItem185 structure."

    value: str | None = ...
    next: ___models_PartitionItem186 | None = ...

@dataclass(kw_only=True)
class PartitionItem186(_SerdeShape):
    "Dataclass for PartitionItem186 structure."

    value: str | None = ...
    next: ___models_PartitionItem187 | None = ...

@dataclass(kw_only=True)
class PartitionItem187(_SerdeShape):
    "Dataclass for PartitionItem187 structure."

    value: str | None = ...
    next: ___models_PartitionItem188 | None = ...

@dataclass(kw_only=True)
class PartitionItem188(_SerdeShape):
    "Dataclass for PartitionItem188 structure."

    value: str | None = ...
    next: ___models_PartitionItem189 | None = ...

@dataclass(kw_only=True)
class PartitionItem189(_SerdeShape):
    "Dataclass for PartitionItem189 structure."

    value: str | None = ...
    next: ___models_PartitionItem190 | None = ...

@dataclass(kw_only=True)
class PartitionItem190(_SerdeShape):
    "Dataclass for PartitionItem190 structure."

    value: str | None = ...
    next: ___models_PartitionItem191 | None = ...

@dataclass(kw_only=True)
class PartitionItem191(_SerdeShape):
    "Dataclass for PartitionItem191 structure."

    value: str | None = ...
    next: ___models_PartitionItem192 | None = ...

@dataclass(kw_only=True)
class PartitionItem192(_SerdeShape):
    "Dataclass for PartitionItem192 structure."

    value: str | None = ...
    next: ___models_PartitionItem193 | None = ...

@dataclass(kw_only=True)
class PartitionItem193(_SerdeShape):
    "Dataclass for PartitionItem193 structure."

    value: str | None = ...
    next: ___models_PartitionItem194 | None = ...

@dataclass(kw_only=True)
class PartitionItem194(_SerdeShape):
    "Dataclass for PartitionItem194 structure."

    value: str | None = ...
    next: ___models_PartitionItem195 | None = ...

@dataclass(kw_only=True)
class PartitionItem195(_SerdeShape):
    "Dataclass for PartitionItem195 structure."

    value: str | None = ...
    next: ___models_PartitionItem196 | None = ...

@dataclass(kw_only=True)
class PartitionItem196(_SerdeShape):
    "Dataclass for PartitionItem196 structure."

    value: str | None = ...
    next: ___models_PartitionItem197 | None = ...

@dataclass(kw_only=True)
class PartitionItem197(_SerdeShape):
    "Dataclass for PartitionItem197 structure."

    value: str | None = ...
    next: ___models_PartitionItem198 | None = ...

@dataclass(kw_only=True)
class PartitionItem198(_SerdeShape):
    "Dataclass for PartitionItem198 structure."

    value: str | None = ...
    next: ___models_PartitionItem199 | None = ...

@dataclass(kw_only=True)
class PartitionItem199(_SerdeShape):
    "Dataclass for PartitionItem199 structure."

    value: str | None = ...
    next: ___models_PartitionItem200 | None = ...

@dataclass(kw_only=True)
class PartitionItem200(_SerdeShape):
    "Dataclass for PartitionItem200 structure."

    value: str | None = ...
    next: ___models_PartitionItem201 | None = ...

@dataclass(kw_only=True)
class PartitionItem201(_SerdeShape):
    "Dataclass for PartitionItem201 structure."

    value: str | None = ...
    next: ___models_PartitionItem202 | None = ...

@dataclass(kw_only=True)
class PartitionItem202(_SerdeShape):
    "Dataclass for PartitionItem202 structure."

    value: str | None = ...
    next: ___models_PartitionItem203 | None = ...

@dataclass(kw_only=True)
class PartitionItem203(_SerdeShape):
    "Dataclass for PartitionItem203 structure."

    value: str | None = ...
    next: ___models_PartitionItem204 | None = ...

@dataclass(kw_only=True)
class PartitionItem204(_SerdeShape):
    "Dataclass for PartitionItem204 structure."

    value: str | None = ...
    next: ___models_PartitionItem205 | None = ...

@dataclass(kw_only=True)
class PartitionItem205(_SerdeShape):
    "Dataclass for PartitionItem205 structure."

    value: str | None = ...
    next: ___models_PartitionItem206 | None = ...

@dataclass(kw_only=True)
class PartitionItem206(_SerdeShape):
    "Dataclass for PartitionItem206 structure."

    value: str | None = ...
    next: ___models_PartitionItem207 | None = ...

@dataclass(kw_only=True)
class PartitionItem207(_SerdeShape):
    "Dataclass for PartitionItem207 structure."

    value: str | None = ...
    next: ___models_PartitionItem208 | None = ...

@dataclass(kw_only=True)
class PartitionItem208(_SerdeShape):
    "Dataclass for PartitionItem208 structure."

    value: str | None = ...
    next: ___models_PartitionItem209 | None = ...

@dataclass(kw_only=True)
class PartitionItem209(_SerdeShape):
    "Dataclass for PartitionItem209 structure."

    value: str | None = ...
    next: ___models_PartitionItem210 | None = ...

@dataclass(kw_only=True)
class PartitionItem210(_SerdeShape):
    "Dataclass for PartitionItem210 structure."

    value: str | None = ...
    next: ___models_PartitionItem211 | None = ...

@dataclass(kw_only=True)
class PartitionItem211(_SerdeShape):
    "Dataclass for PartitionItem211 structure."

    value: str | None = ...
    next: ___models_PartitionItem212 | None = ...

@dataclass(kw_only=True)
class PartitionItem212(_SerdeShape):
    "Dataclass for PartitionItem212 structure."

    value: str | None = ...
    next: ___models_PartitionItem213 | None = ...

@dataclass(kw_only=True)
class PartitionItem213(_SerdeShape):
    "Dataclass for PartitionItem213 structure."

    value: str | None = ...
    next: ___models_PartitionItem214 | None = ...

@dataclass(kw_only=True)
class PartitionItem214(_SerdeShape):
    "Dataclass for PartitionItem214 structure."

    value: str | None = ...
    next: ___models_PartitionItem215 | None = ...

@dataclass(kw_only=True)
class PartitionItem215(_SerdeShape):
    "Dataclass for PartitionItem215 structure."

    value: str | None = ...
    next: ___models_PartitionItem216 | None = ...

@dataclass(kw_only=True)
class PartitionItem216(_SerdeShape):
    "Dataclass for PartitionItem216 structure."

    value: str | None = ...
    next: ___models_PartitionItem217 | None = ...

@dataclass(kw_only=True)
class PartitionItem217(_SerdeShape):
    "Dataclass for PartitionItem217 structure."

    value: str | None = ...
    next: ___models_PartitionItem218 | None = ...

@dataclass(kw_only=True)
class PartitionItem218(_SerdeShape):
    "Dataclass for PartitionItem218 structure."

    value: str | None = ...
    next: ___models_PartitionItem219 | None = ...

@dataclass(kw_only=True)
class PartitionItem219(_SerdeShape):
    "Dataclass for PartitionItem219 structure."

    value: str | None = ...
    next: ___models_PartitionItem220 | None = ...

@dataclass(kw_only=True)
class PartitionItem220(_SerdeShape):
    "Dataclass for PartitionItem220 structure."

    value: str | None = ...
    next: ___models_PartitionItem221 | None = ...

@dataclass(kw_only=True)
class PartitionItem221(_SerdeShape):
    "Dataclass for PartitionItem221 structure."

    value: str | None = ...
    next: ___models_PartitionItem222 | None = ...

@dataclass(kw_only=True)
class PartitionItem222(_SerdeShape):
    "Dataclass for PartitionItem222 structure."

    value: str | None = ...
    next: ___models_PartitionItem223 | None = ...

@dataclass(kw_only=True)
class PartitionItem223(_SerdeShape):
    "Dataclass for PartitionItem223 structure."

    value: str | None = ...
    next: ___models_PartitionItem224 | None = ...

@dataclass(kw_only=True)
class PartitionItem224(_SerdeShape):
    "Dataclass for PartitionItem224 structure."

    value: str | None = ...
    next: ___models_PartitionItem225 | None = ...

@dataclass(kw_only=True)
class PartitionItem225(_SerdeShape):
    "Dataclass for PartitionItem225 structure."

    value: str | None = ...
    next: ___models_PartitionItem226 | None = ...

@dataclass(kw_only=True)
class PartitionItem226(_SerdeShape):
    "Dataclass for PartitionItem226 structure."

    value: str | None = ...
    next: ___models_PartitionItem227 | None = ...

@dataclass(kw_only=True)
class PartitionItem227(_SerdeShape):
    "Dataclass for PartitionItem227 structure."

    value: str | None = ...
    next: ___models_PartitionItem228 | None = ...

@dataclass(kw_only=True)
class PartitionItem228(_SerdeShape):
    "Dataclass for PartitionItem228 structure."

    value: str | None = ...
    next: ___models_PartitionItem229 | None = ...

@dataclass(kw_only=True)
class PartitionItem229(_SerdeShape):
    "Dataclass for PartitionItem229 structure."

    value: str | None = ...
    next: ___models_PartitionItem230 | None = ...

@dataclass(kw_only=True)
class PartitionItem230(_SerdeShape):
    "Dataclass for PartitionItem230 structure."

    value: str | None = ...
    next: ___models_PartitionItem231 | None = ...

@dataclass(kw_only=True)
class PartitionItem231(_SerdeShape):
    "Dataclass for PartitionItem231 structure."

    value: str | None = ...
    next: ___models_PartitionItem232 | None = ...

@dataclass(kw_only=True)
class PartitionItem232(_SerdeShape):
    "Dataclass for PartitionItem232 structure."

    value: str | None = ...
    next: ___models_PartitionItem233 | None = ...

@dataclass(kw_only=True)
class PartitionItem233(_SerdeShape):
    "Dataclass for PartitionItem233 structure."

    value: str | None = ...
    next: ___models_PartitionItem234 | None = ...

@dataclass(kw_only=True)
class PartitionItem234(_SerdeShape):
    "Dataclass for PartitionItem234 structure."

    value: str | None = ...
    next: ___models_PartitionItem235 | None = ...

@dataclass(kw_only=True)
class PartitionItem235(_SerdeShape):
    "Dataclass for PartitionItem235 structure."

    value: str | None = ...
    next: ___models_PartitionItem236 | None = ...

@dataclass(kw_only=True)
class PartitionItem236(_SerdeShape):
    "Dataclass for PartitionItem236 structure."

    value: str | None = ...
    next: ___models_PartitionItem237 | None = ...

@dataclass(kw_only=True)
class PartitionItem237(_SerdeShape):
    "Dataclass for PartitionItem237 structure."

    value: str | None = ...
    next: ___models_PartitionItem238 | None = ...

@dataclass(kw_only=True)
class PartitionItem238(_SerdeShape):
    "Dataclass for PartitionItem238 structure."

    value: str | None = ...
    next: ___models_PartitionItem239 | None = ...

@dataclass(kw_only=True)
class PartitionItem239(_SerdeShape):
    "Dataclass for PartitionItem239 structure."

    value: str | None = ...
    next: ___models_PartitionItem240 | None = ...

@dataclass(kw_only=True)
class PartitionItem240(_SerdeShape):
    "Dataclass for PartitionItem240 structure."

    value: str | None = ...
    next: ___models_PartitionItem241 | None = ...

@dataclass(kw_only=True)
class PartitionItem241(_SerdeShape):
    "Dataclass for PartitionItem241 structure."

    value: str | None = ...
    next: PartitionItem242 | None = ...
