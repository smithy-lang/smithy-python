#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from threading import Lock
from typing import Self


class PureChecksum:
    """Base class for the pure-Python implementations.

    Each method holds a lock, so an instance can be shared between threads like the
    native implementations and :mod:`hashlib` objects can. Subclasses implement the
    underscored methods, which are only called with the lock held.
    """

    __slots__ = ("_lock",)

    def __init__(self) -> None:
        self._lock = Lock()

    def update(self, data: bytes | bytearray | memoryview, /) -> None:
        with self._lock:
            self._update(data)

    def digest(self) -> bytes:
        with self._lock:
            return self._digest()

    def copy(self) -> Self:
        with self._lock:
            return self._copy()

    def _update(self, data: bytes | bytearray | memoryview) -> None:
        raise NotImplementedError

    def _digest(self) -> bytes:
        raise NotImplementedError

    def _copy(self) -> Self:
        raise NotImplementedError
