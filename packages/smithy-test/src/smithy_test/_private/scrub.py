#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from collections.abc import Callable, Iterable

from .errors import HTTPRecordError

type TextScrubber = Callable[[str], str]

# The fictitious account IDs of AWSSharedContent, which the AWS documentation
# standards approve for examples.
APPROVED_ACCOUNT_IDS = (
    "123456789012",
    "111122223333",
    "444455556666",
    "777788889999",
    "000000000000",
    "111111111111",
    "222222222222",
    "333333333333",
    "444444444444",
    "555555555555",
    "666666666666",
    "777777777777",
    "888888888888",
    "999999999999",
)

_DROPPED_HEADERS = frozenset(
    {
        "authorization",
        "date",
        "proxy-authenticate",
        "set-cookie",
        "x-amz-security-token",
        "x-amzn-trace-id",
    }
)
_PLACEHOLDER_HEADERS = {
    "x-amz-id-2": "RECORDED-HOST-ID",
    "x-amz-request-id": "RECORDED-REQUEST-ID",
    "x-amz-sts-extended-request-id": "RECORDED-REQUEST-ID",
    "x-amzn-requestid": "RECORDED-REQUEST-ID",
}
# A payload covered by a checksum or digest can't change without failing validation.
_INTEGRITY_HEADER = re.compile(r"^(x-amz-checksum-.*|content-md5)$")
_STRUCTURED_TYPE = re.compile(
    r"(json|xml|x-www-form-urlencoded|text/html|text/csv)", re.IGNORECASE
)

# Not inside a longer number or a decimal, such as a timestamp written as 1.795550537012E9.
_ACCOUNT_ID = re.compile(r"(?<![\d.])\d{12}(?!\d|\.\d|[eE][+-]?\d)")
_ACCESS_KEY_ID = re.compile(
    r"\b(?:AKIA|ASIA|AIDA|AROA|AGPA|ANPA|ANVA|APKA)[A-Z0-9]{16,17}\b"
)
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_UUID_HOLE = re.compile("\x00(\\d+)\x00")
_ASSUMED_ROLE = re.compile(r"assumed-role/([^/\s\"<>]+)/([^\s\"<>]+)")
_ROLE_ID_SESSION = re.compile(r"\b((?:AROA|AIDA)[A-Z0-9]{16,}):([^\s\"<>]+)")
_USER_NAME = re.compile(r"(:(?:user|federated-user)/)([^\s\"<>]+)")
_SENSITIVE_FIELD = (
    r"(?:secret_?access_?key|session_?token|secret_?key|id_?token|access_?token"
    r"|refresh_?token|client_?secret|password)"
)
_SECRET_JSON = re.compile(rf'("{_SENSITIVE_FIELD}"\s*:\s*")([^"]*)(")', re.IGNORECASE)
_SECRET_XML = re.compile(rf"(<{_SENSITIVE_FIELD}>)([^<]*)(</)", re.IGNORECASE)


class Scrubber:
    """Replaces what identifies an account or grants access in recorded responses.

    Replacements are stable within one scrubber, so a value that appears in several
    responses of a recording still matches itself. The patterns are a best effort:
    recordings must be reviewed before they're committed.
    """

    def __init__(self, extra: Iterable[TextScrubber] = ()) -> None:
        self._extra = tuple(extra)
        self._pseudonyms: dict[str, str] = {}
        self._known: list[str] = []
        self._accounts = 0
        self._uuids: dict[str, str] = {}

    def add_known(self, value: str) -> None:
        """Replace every occurrence of a value that must not appear in a recording."""
        if value and value not in self._known:
            self._known.append(value)
            # Longest first, so a value that contains another isn't left in pieces.
            self._known.sort(key=len, reverse=True)

    def headers(self, headers: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
        """Drop or replace headers that identify a request or session."""
        scrubbed: list[tuple[str, str]] = []
        for name, value in headers:
            lowered = name.lower()
            if lowered in _DROPPED_HEADERS:
                continue
            if lowered in _PLACEHOLDER_HEADERS:
                scrubbed.append((name, _PLACEHOLDER_HEADERS[lowered]))
            else:
                scrubbed.append((name, self.text(value)))
        return scrubbed

    def kind(self, headers: Iterable[tuple[str, str]]) -> str | None:
        """Tell ``json`` or ``xml`` for a body that's safe to reformat, else None."""
        fields = {name.lower(): value for name, value in headers}
        if any(_INTEGRITY_HEADER.match(name) for name in fields):
            return None
        content_type = fields.get("content-type", "").lower()
        if "json" in content_type:
            return "json"
        if "xml" in content_type:
            return "xml"
        return None

    def body(self, headers: Iterable[tuple[str, str]], body: bytes) -> bytes:
        """Scrub a body that is structured text and not covered by an integrity header."""
        fields = {name.lower(): value for name, value in headers}
        if any(_INTEGRITY_HEADER.match(name) for name in fields):
            return body
        if not _STRUCTURED_TYPE.search(fields.get("content-type", "")):
            return body
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return body
        return self.text(text).encode("utf-8")

    def text(self, text: str) -> str:
        """Scrub identifying values out of text, keeping every replacement's length."""
        # UUIDs are set aside first, since their last group can look like an account ID.
        held: list[str] = []
        text = _UUID.sub(lambda m: self._hold_uuid(m[0], held), text)
        for value in self._known:
            if value in text:
                text = text.replace(
                    value, self._replace(value, self._known_kind(value))
                )
        text = _SECRET_JSON.sub(lambda m: f"{m[1]}REDACTED{m[3]}", text)
        text = _SECRET_XML.sub(lambda m: f"{m[1]}REDACTED{m[3]}", text)
        text = _ASSUMED_ROLE.sub(
            lambda m: (
                f"assumed-role/{_fill('Recorder', len(m[1]))}/"
                f"{_fill('recorded-session', len(m[2]))}"
            ),
            text,
        )
        text = _ROLE_ID_SESSION.sub(
            lambda m: f"{m[1]}:{_fill('recorded-session', len(m[2]))}", text
        )
        text = _USER_NAME.sub(
            lambda m: f"{m[1]}{_fill('recorded-user', len(m[2]))}", text
        )
        text = _ACCESS_KEY_ID.sub(
            lambda m: self._replace(m[0], self._key_id(m[0])), text
        )
        text = _ACCOUNT_ID.sub(lambda m: self._replace(m[0], self._account_id), text)
        text = _IPV4.sub(lambda m: self._replace(m[0], self._address), text)
        text = _EMAIL.sub(lambda m: self._replace(m[0], self._email), text)
        text = _UUID_HOLE.sub(lambda m: held[int(m[1])], text)
        for scrub in self._extra:
            text = scrub(text)
        return text

    def _hold_uuid(self, original: str, held: list[str]) -> str:
        key = original.lower()
        if key not in self._uuids:
            self._uuids[key] = f"00000000-0000-4000-8000-{len(self._uuids) + 1:012d}"
        held.append(self._uuids[key])
        return f"\x00{len(held) - 1}\x00"

    def _replace(self, original: str, make: Callable[[int], str]) -> str:
        if original not in self._pseudonyms:
            self._pseudonyms[original] = make(len(self._pseudonyms) + 1)
        return self._pseudonyms[original]

    def _known_kind(self, value: str) -> Callable[[int], str]:
        if _ACCOUNT_ID.fullmatch(value):
            return self._account_id
        if _ACCESS_KEY_ID.fullmatch(value):
            return self._key_id(value)
        return lambda n: f"REDACTED-{n}"

    def _account_id(self, _: int) -> str:
        if self._accounts == len(APPROVED_ACCOUNT_IDS):
            raise HTTPRecordError(
                f"The recording has more than {len(APPROVED_ACCOUNT_IDS)} distinct "
                "account IDs, and only that many approved example IDs exist."
            )
        self._accounts += 1
        return APPROVED_ACCOUNT_IDS[self._accounts - 1]

    @staticmethod
    def _key_id(original: str) -> Callable[[int], str]:
        digits = len(original) - len("AKIARECORDED")
        return lambda n: f"{original[:4]}RECORDED{n:0{digits}d}"

    @staticmethod
    def _address(n: int) -> str:
        # The documentation range, which never routes anywhere.
        return f"192.0.2.{n % 254 + 1}"

    @staticmethod
    def _email(n: int) -> str:
        return f"user{n}@example.com"


def _fill(seed: str, length: int) -> str:
    """Repeat a seed to exactly ``length`` characters."""
    return (seed * (length // len(seed) + 1))[:length]
