#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import base64
import inspect
import json
import os
import re
import runpy
import zlib
from ast import literal_eval
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from inspect import cleandoc
from pathlib import Path
from types import FrameType
from typing import Any, Literal
from urllib.parse import quote

from .errors import HTTPRecordError
from .http_mock import CURRENT_OPERATION
from .scrub import Scrubber, TextScrubber

MODE_ENV = "SMITHY_PYTHON_TEST_MODE"

type RecordMode = Literal["record", "playback"]
_EVENT_STREAM = "application/vnd.amazon.eventstream"
_CREDENTIAL = re.compile(r"Credential=([A-Za-z0-9]+)/")
_MIN_KNOWN = 6
_SECRET_FIELDS = ("secret_access_key", "session_token")
_IDENTITY_FIELDS = (
    ("the access key ID", "access_key_id"),
    ("the secret access key", "secret_access_key"),
    ("the session token", "session_token"),
    ("the account ID", "account_id"),
)


_LITERAL_PAD = " " * 16
_DECLARATION = re.compile(r"^\s*(<\?xml[^>]*\?>)")


@dataclass(frozen=True)
class RecordedResponse:
    operation: str
    status: int
    headers: dict[str, str]
    body: bytes
    literal: str | None = None
    """The body as a pretty-printed, indented string literal, if it has one."""


class ResponseLog:
    """The scrubbed responses of a recording session, in the order they arrived."""

    def __init__(
        self, scrubbers: Iterable[TextScrubber] = (), redact: Iterable[str] = ()
    ) -> None:
        self._scrubber = Scrubber(scrubbers)
        self._known: list[tuple[str, str]] = []
        self._secrets: list[tuple[str, set[str]]] = []
        self._refusal: HTTPRecordError | None = None
        self.responses: list[RecordedResponse] = []
        for number, value in enumerate(redact, start=1):
            self._know(f"redact value {number}", value)

    def learn(self, headers: Iterable[tuple[str, str]]) -> None:
        """Take the access key ID and session token out of a signed request's headers.

        They then can't appear in a recording, and the recording is refused if they do.
        """
        for name, value in headers:
            lowered = name.lower()
            if lowered == "authorization" and (m := _CREDENTIAL.search(value)):
                self._know("the access key ID", m.group(1))
            elif lowered == "x-amz-security-token":
                self._know_secret("the session token", value)

    def learn_identity(self, identity: Any) -> None:
        """Take the secrets and the account ID out of a resolved credentials identity."""
        for label, attribute in _IDENTITY_FIELDS:
            value = getattr(identity, attribute, None)
            if not isinstance(value, str):
                continue
            if attribute in _SECRET_FIELDS:
                self._know_secret(label, value)
            else:
                self._know(label, value)

    def check(self, headers: list[tuple[str, str]]) -> None:
        """Reject a response before its body is read.

        :raises HTTPRecordError: If no operation is in flight or the response is an
            event stream, whose body may never end.
        """
        operation = _operation()
        for name, value in headers:
            if name.lower() == "content-type" and value.startswith(_EVENT_STREAM):
                raise HTTPRecordError(
                    f"{operation} returned an event stream, which can't be recorded."
                )

    def add(self, status: int, headers: list[tuple[str, str]], body: bytes) -> None:
        """Scrub and keep a response of the operation in flight."""
        operation = _operation()
        for name, value in headers:
            self._refuse_secrets(operation, f"the {name} header", f"{name}\n{value}")
        self._refuse_secrets(operation, "the body", body.decode("utf-8", "replace"))
        kept = self._scrubber.headers(headers)
        scrubbed = self._scrubber.body(headers, body)
        merged: dict[str, str] = {}
        for name, value in kept:
            merged[name] = f"{merged[name]}, {value}" if name in merged else value
        literal = None
        if (kind := self._scrubber.kind(headers)) is not None:
            pretty = _pretty(kind, scrubbed)
            if pretty is not None and (literal := _literal(pretty)) is not None:
                scrubbed = pretty.encode("utf-8")
        if scrubbed != body:
            for name in merged:
                lowered = name.lower()
                if lowered == "content-length":
                    merged[name] = str(len(scrubbed))
                # DynamoDB's checksum of the body, which the client may verify.
                elif lowered == "x-amz-crc32" and merged[name] == str(zlib.crc32(body)):
                    merged[name] = str(zlib.crc32(scrubbed))
        for name, value in merged.items():
            self._refuse_leaks(operation, f"the {name} header", f"{name}\n{value}")
        self._refuse_leaks(operation, "the body", scrubbed.decode("utf-8", "replace"))
        self.responses.append(
            RecordedResponse(operation, status, merged, scrubbed, literal)
        )

    def source(self) -> str:
        """Render the responses as a module that installs them on a mock controller.

        :raises HTTPRecordError: If a response held a secret or a value to redact that
            couldn't be replaced, even if the error was caught.
        """
        if self._refusal is not None:
            raise self._refusal
        by_operation: dict[str, list[RecordedResponse]] = {}
        for response in self.responses:
            by_operation.setdefault(response.operation, []).append(response)
        uses_literal = any(r.literal is not None for r in self.responses)
        lines = [
            "# Recorded by smithy_test. Review it for anything identifying before "
            "committing.",
            *(["from inspect import cleandoc", ""] if uses_literal else []),
            "from smithy_test import HTTPMockController",
            "",
            "",
            "def install(controller: HTTPMockController) -> None:",
        ]
        if not by_operation:
            lines.append("    pass")
        for operation, responses in by_operation.items():
            lines += [
                "    (",
                f"        controller.expect_operation({operation!r})",
                f"        .times({len(responses)})",
            ]
            for response in responses:
                lines.append("        .respond_with(")
                lines.append(f"            status_code={response.status},")
                if response.headers:
                    lines.append("            headers={")
                    lines += [
                        f"                {name!r}: {value!r},"
                        for name, value in response.headers.items()
                    ]
                    lines.append("            },")
                if response.literal is None:
                    lines.append(f"            body={response.body!r},")
                else:
                    lines.append("            body=cleandoc(")
                    lines.append(f'                r"""{response.literal}"""')
                    lines.append("            ),")
                lines.append("        )")
            lines.append("    )")
        source = "\n".join(lines) + "\n"
        self._refuse_leaks("recorded", "the recording", source)
        self._refuse_secrets("recorded", "the recording", source)
        return source

    def write(self, path: str | Path) -> None:
        source = self.source()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")

    def _know(self, label: str, value: str) -> None:
        if len(value) >= _MIN_KNOWN and all(v != value for _, v in self._known):
            self._known.append((label, value))
            self._scrubber.add_known(value)

    def _know_secret(self, label: str, value: str) -> None:
        if len(value) >= _MIN_KNOWN and all(
            label != known for known, _ in self._secrets
        ):
            self._secrets.append((label, _forms(value)))

    def _refuse(self, message: str) -> None:
        # Kept so that a test that catches the error can't still write a recording.
        self._refusal = self._refusal or HTTPRecordError(message)
        raise HTTPRecordError(message)

    def _refuse_secrets(self, operation: str, where: str, text: str) -> None:
        for label, forms in self._secrets:
            if any(form in text for form in forms):
                self._refuse(
                    f"The {operation} response has {label} in {where}. Secrets are "
                    "never recorded, and a service echoing one back is worth "
                    "investigating, so nothing was recorded."
                )

    def _refuse_leaks(self, operation: str, where: str, text: str) -> None:
        for label, value in self._known:
            if any(form in text for form in _forms(value)):
                self._refuse(
                    f"The {operation} response has {label} in {where}, where it can't "
                    "be replaced, so nothing was recorded."
                )


def resolve_mode(mode: str | None) -> RecordMode:
    """Pick the mode: the argument if given, else the environment, else playback.

    :raises ValueError: If the chosen mode isn't ``record`` or ``playback``.
    """
    source = "mode" if mode is not None else MODE_ENV
    chosen = mode if mode is not None else os.environ.get(MODE_ENV) or "playback"
    if chosen not in ("record", "playback"):
        raise ValueError(f"{source} must be 'record' or 'playback', got {chosen!r}.")
    return chosen


def load_installer(path: str | Path) -> Callable[[Any], None]:
    """Load the ``install`` function of a recording module.

    :raises HTTPRecordError: If there's no recording at the path.
    """
    target = Path(path)
    if not target.is_file():
        raise HTTPRecordError(
            f"No recording at {target}. Run the test with {MODE_ENV}=record against the "
            "live service to create it."
        )
    return runpy.run_path(str(target))["install"]


def default_recording_path(client: object, frames_up: int) -> Path:
    """Name a recording after the calling test function and the client.

    :param frames_up: How many frames up from the caller of this function the test is.
    :raises ValueError: If the caller has no source file or isn't a named function.
    """
    frame: FrameType | None = inspect.currentframe()
    for _ in range(frames_up + 1):
        frame = frame.f_back if frame is not None else None
    file = frame.f_globals.get("__file__") if frame is not None else None
    function = frame.f_code.co_name if frame is not None else "<module>"
    if not isinstance(file, str) or function.startswith("<"):
        raise ValueError(
            "A recording path can only be inferred for a call made inside a named "
            "function of a source file. Pass the path."
        )
    return Path(file).parent / "recordings" / function / f"{_client_name(client)}.py"


def _operation() -> str:
    operation = CURRENT_OPERATION.get()
    if operation is None:
        raise HTTPRecordError("A request was sent outside of an operation call.")
    return operation


def _pretty(kind: str, body: bytes) -> str | None:
    """Reformat a JSON or XML body with indentation, or None if that could change it."""
    try:
        text = body.decode("utf-8")
        if kind == "json":
            value = json.loads(text)
            pretty = json.dumps(value, indent=2, ensure_ascii=False)
            return pretty if json.loads(pretty) == value else None
        # Imported here because xml.sax reads an environment variable on import.
        from xml.dom import minidom
        from xml.etree import ElementTree

        declaration = _DECLARATION.match(text)
        # The body is a response from the service the test just called.
        document = minidom.parseString(body).toprettyxml(indent="  ")  # noqa: S318
        # minidom writes its own declaration, which drops the encoding.
        lines = document.split("\n")[1:]
        if declaration:
            lines.insert(0, declaration.group(1))
        pretty = "\n".join(line for line in lines if line.strip()).strip()
        same = ElementTree.canonicalize(text, strip_text=True) == (
            ElementTree.canonicalize(pretty, strip_text=True)
        )
        return pretty if same else None
    except Exception:
        return None


def _literal(text: str) -> str | None:
    """Lay text out for a raw triple-quoted string that ``cleandoc`` reads back as is."""
    if '"""' in text or any(ord(c) < 32 and c != "\n" for c in text):
        return None
    lines = (f"{_LITERAL_PAD}{line}" if line else "" for line in text.split("\n"))
    inner = "\n" + "\n".join(lines) + "\n" + _LITERAL_PAD
    if cleandoc(inner) != text or literal_eval(f'r"""{inner}"""') != inner:
        return None
    return inner


def _forms(value: str) -> set[str]:
    """The ways a secret can be spelled in a header or body, as text."""
    raw = value.encode("utf-8")
    return {
        value,
        quote(value, safe=""),
        quote(value),
        json.dumps(value)[1:-1],
        _xml_escape(value),
        base64.b64encode(raw).decode("ascii").rstrip("="),
        base64.urlsafe_b64encode(raw).decode("ascii").rstrip("="),
    }


def _xml_escape(value: str) -> str:
    for char, entity in (
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&apos;"),
    ):
        value = value.replace(char, entity)
    return value


def _client_name(client: object) -> str:
    name = type(client).__name__.removeprefix("Async").removesuffix("Client")
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    return snake.lower() or "client"
