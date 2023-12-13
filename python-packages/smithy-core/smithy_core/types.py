#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

Document: TypeAlias = (
    Mapping[str, "Document"] | Sequence["Document"] | str | int | float | bool | None
)


class JsonString(str):
    """A string that contains json data which can be lazily loaded."""

    _json = None

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self)
        return self._json

    @staticmethod
    def from_json(j: Any) -> "JsonString":
        json_string = JsonString(json.dumps(j))
        json_string._json = j
        return json_string


class JsonBlob(bytes):
    """Bytes that contain json data which can be lazily loaded."""

    _json = None

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self.decode(encoding="utf-8"))
        return self._json

    @staticmethod
    def from_json(j: Any) -> "JsonBlob":
        json_string = JsonBlob(json.dumps(j).encode(encoding="utf-8"))
        json_string._json = j
        return json_string
