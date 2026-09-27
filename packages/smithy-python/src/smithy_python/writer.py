# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Structured annotation writing for a single Python module."""

from __future__ import annotations

from collections import Counter
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from unicodedata import normalize

from .exceptions import CodegenError
from .symbols import TypeReference

# Union of Python 3.12-3.15 builtins, including platform-specific names.
# Keep this fixed so import planning does not depend on the generator host.
_BUILTINS = frozenset(
    "ArithmeticError AssertionError AttributeError BaseException BaseExceptionGroup "
    "BlockingIOError BrokenPipeError BufferError BytesWarning ChildProcessError "
    "ConnectionAbortedError ConnectionError ConnectionRefusedError ConnectionResetError "
    "DeprecationWarning EOFError Ellipsis EncodingWarning EnvironmentError Exception "
    "ExceptionGroup False FileExistsError FileNotFoundError FloatingPointError "
    "FutureWarning GeneratorExit IOError ImportCycleError ImportError ImportWarning IndentationError "
    "IndexError InterruptedError IsADirectoryError KeyError KeyboardInterrupt "
    "LookupError MemoryError ModuleNotFoundError NameError None NotADirectoryError "
    "NotImplemented NotImplementedError OSError OverflowError PendingDeprecationWarning "
    "PermissionError ProcessLookupError PythonFinalizationError RecursionError ReferenceError ResourceWarning "
    "RuntimeError RuntimeWarning StopAsyncIteration StopIteration SyntaxError "
    "SyntaxWarning SystemError SystemExit TabError TimeoutError True TypeError "
    "UnboundLocalError UnicodeDecodeError UnicodeEncodeError UnicodeError "
    "UnicodeTranslateError UnicodeWarning UserWarning ValueError Warning WindowsError "
    "ZeroDivisionError _IncompleteInputError __build_class__ __debug__ __doc__ __import__ __lazy_import__ __loader__ "
    "__name__ __package__ __spec__ abs aiter all anext any ascii bin bool breakpoint "
    "bytearray bytes callable chr classmethod compile complex copyright credits "
    "delattr dict dir divmod enumerate eval exec exit filter float format frozendict frozenset "
    "getattr globals hasattr hash help hex id input int isinstance issubclass iter "
    "len license list locals map max memoryview min next object oct open ord pow "
    "print property quit range repr reversed round sentinel set setattr slice sorted "
    "staticmethod str sum super tuple type vars zip".split()
)


def _binding(name: str) -> str:
    """Compare names as Python binds them, without changing emitted spelling."""
    return normalize("NFKC", name)


class PythonWriter:
    """Write trusted Python lines, retaining type references until rendering."""

    def __init__(
        self,
        module: str,
        *,
        declarations: Iterable[str] = (),
        local_names: Iterable[str] = (),
    ) -> None:
        self._module = module
        self._declarations: set[str] = set()
        for name in declarations:
            binding = _binding(name)
            if binding in self._declarations:
                raise CodegenError(f"Duplicate generated declaration: {name!r}")
            self._declarations.add(binding)
        self._local_names = frozenset(_binding(name) for name in local_names)
        self._depth = 0
        self._lines: list[tuple[int, tuple[str | TypeReference, ...]]] = []

    def line(self, *parts: str | TypeReference) -> None:
        """Append one line, concatenating its parts without separators."""
        self._lines.append((self._depth, parts))

    @contextmanager
    def indent(self) -> Generator[None]:
        """Indent by four spaces for the duration of the block."""
        self._depth += 1
        try:
            yield
        finally:
            self._depth -= 1

    def _plan_imports(self) -> tuple[dict[tuple[str | None, str], str], list[str]]:
        identities: set[tuple[str | None, str]] = set()
        pending = [
            part
            for _, parts in self._lines
            for part in parts
            if isinstance(part, TypeReference)
        ]
        while pending:
            ref = pending.pop()
            if ref.module is None and (ref.name != "None" or ref.arguments):
                raise CodegenError(
                    f"Only the None literal may omit its module: {ref.name!r}"
                )
            identities.add((ref.module, ref.name))
            pending.extend(ref.arguments)
        current_names = {
            _binding(name) for module, name in identities if module == self._module
        }
        for name in sorted(current_names & self._local_names):
            raise CodegenError(
                f"Same-module reference {self._module}.{name} conflicts with local name {name!r}"
            )
        reserved = self._declarations | self._local_names | current_names
        external = sorted(
            (module, name)
            for module, name in identities
            if module is not None and module not in ("builtins", self._module)
        )
        counts = Counter(_binding(name) for _, name in external)
        names: dict[tuple[str | None, str], str] = {}
        imports: list[tuple[str, str, str, str]] = []
        for module, name in external:
            alias = (
                f"_{module.replace('.', '_')}_{name}"
                if _binding(name) in reserved
                or _binding(name) in _BUILTINS
                or _binding(name) == "annotations"
                or counts[_binding(name)] > 1
                else name
            )
            names[(module, name)] = alias
            suffix = f" as {alias}" if alias != name else ""
            imports.append(
                (module, name, alias, f"from {module} import {name}{suffix}")
            )
        qualify_builtins = False
        for module, name in identities:
            if module is None:
                names[(module, name)] = "None"
            elif module == "builtins":
                shadowed = _binding(name) in reserved
                names[(module, name)] = f"_builtins.{name}" if shadowed else name
                qualify_builtins |= shadowed
            elif module == self._module:
                names[(module, name)] = name
        if qualify_builtins:
            imports.append(
                ("builtins", "", "_builtins", "import builtins as _builtins")
            )

        # Check the complete plan, including unaliased imports. No binding gets
        # priority merely because its reference was encountered first.
        bindings = dict.fromkeys(reserved, "a generated declaration or local name")
        imports.sort()
        for module, name, alias, _ in imports:
            owner = f"{module}.{name}" if name else module
            binding = _binding(alias)
            if binding in bindings or binding in _BUILTINS:
                conflict = bindings.get(binding, "a builtin")
                raise CodegenError(
                    f"Import binding {alias!r} for {owner} conflicts with {conflict}"
                )
            bindings[binding] = owner
        return names, [statement for _, _, _, statement in imports]

    @staticmethod
    def _annotation(
        reference: TypeReference, names: dict[tuple[str | None, str], str]
    ) -> str:
        # Emit tokens rather than recursing through potentially deep collections.
        pending: list[str | TypeReference] = [reference]
        result: list[str] = []
        while pending:
            part = pending.pop()
            if isinstance(part, str):
                result.append(part)
                continue
            if part.module is None:
                result.append("None")
                continue
            result.append(names[(part.module, part.name)])
            if part.nullable:
                pending.append(" | None")
            if part.arguments:
                pending.append("]")
                for index in range(len(part.arguments) - 1, -1, -1):
                    pending.append(part.arguments[index])
                    if index:
                        pending.append(", ")
                pending.append("[")
        return "".join(result)

    def render(self) -> str:
        """Return complete source without changing the recorded lines."""
        names, imports = self._plan_imports()
        header = "from __future__ import annotations\n"
        if imports:
            header += "\n" + "\n".join(imports) + "\n"
        body: list[str] = []
        for depth, parts in self._lines:
            text = "".join(
                part if isinstance(part, str) else self._annotation(part, names)
                for part in parts
            )
            body.append("    " * depth + text if text else "")
        return header + ("\n\n" + "\n".join(body) + "\n" if body else "")
