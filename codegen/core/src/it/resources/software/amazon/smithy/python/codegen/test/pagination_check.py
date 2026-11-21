# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Checks the paginators of the client generated from pagination.smithy.

Usage: python3 pagination_check.py <generated project directory>

The generated clients are parsed, imported in a fresh interpreter to check what
importing loads, and type checked from consumer modules with strict Pyright.
Then they are driven offline: a recording transport answers each request with
the next canned JSON response, so every page goes through the ordinary operation
method, its plugins and the request pipeline.
"""

import ast
import asyncio
import copy
import dataclasses
import inspect
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from urllib.parse import parse_qsl

ROOT = Path(sys.argv[1])
SOURCE = ROOT / "src"
sys.path.insert(0, str(SOURCE))

import smithy_core  # noqa: E402
from smithy_core.aio.pagination import AsyncItemPaginator, AsyncPaginator  # noqa: E402
from smithy_core.aio.types import AsyncBytesReader  # noqa: E402
from smithy_core.pagination import ItemPaginator, Paginator  # noqa: E402
from smithy_core.retries import SimpleRetryStrategy  # noqa: E402
from smithy_http import HTTPResponse, tuples_to_fields  # noqa: E402

FAILURES = []

# Each paginator, by the method of the operation it iterates.
PAGINATORS = {
    "paginate_list_things": "list_things",
    "paginate_scan_items": "scan_items",
    "paginate_count": "count",
    "paginate_inspect": "inspect",
    "paginate_list_books": "list_books",
    # paginate_foo is PaginateFoo's own method, so Foo's paginator takes the next
    # free name.
    "paginate_foo_": "foo",
    "paginate_paginate_foo": "paginate_foo",
    "paginate_close_": "close_",
    "paginate_poll": "poll",
}
# Operation methods that are named like paginators.
OPERATIONS = {"paginate_foo"}
# Each paginator's runtime type, and its type arguments as written.
RETURNS = {
    "paginate_list_things": (
        "ItemPaginator",
        "_models.ListThingsOutput, _models.Thing",
    ),
    "paginate_scan_items": (
        "ItemPaginator",
        "_models.ScanItemsOutput, tuple[str, _models.Plugin | None]",
    ),
    # The clients, and a model, are named like these runtime types.
    "paginate_count": ("Paginator", "_models.CountOutput"),
    "paginate_inspect": (
        "ItemPaginator",
        "_models.InspectOutput, list[_models.AsyncItemPaginator] | None",
    ),
    "paginate_list_books": ("ItemPaginator", "_models.ListBooksOutput, str"),
    "paginate_foo_": ("Paginator", "_models.FooOutput"),
    "paginate_paginate_foo": ("Paginator", "_models.PaginateFooOutput"),
    "paginate_close_": ("Paginator", "_models.CloseOutput"),
    "paginate_poll": ("Paginator", "_models.PollOutput"),
}


def check(condition, message):
    if not condition:
        FAILURES.append(message)


def equal(actual, expected, what):
    check(
        actual == expected,
        "%s:\n  expected %r\n  actual   %r" % (what, expected, actual),
    )


# --- The generated definitions -------------------------------------------------


def is_overload(node):
    return any(
        getattr(decorator, "id", getattr(decorator, "attr", "")).endswith("overload")
        for decorator in node.decorator_list
    )


def bindings(tree):
    """Maps each name the module imports, at runtime or for type checking, to where
    it is imported from."""
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                found.setdefault(alias.asname or alias.name, []).append(
                    module + "." + alias.name
                )
    return found


def check_definitions():
    for label, path, client, runtime in (
        ("sync", "client.py", "Paginator", "smithy_core.pagination."),
        (
            "async",
            "aio/client.py",
            "AsyncPaginator",
            "smithy_core.aio.pagination.Async",
        ),
    ):
        tree = ast.parse((SOURCE / "pages" / path).read_text(encoding="utf-8"))
        imported = bindings(tree)
        # The client class is defined here, so the runtime type it is named like
        # must be imported under another name.
        for name in {n.name for n in tree.body if isinstance(n, ast.ClassDef)}:
            imported.setdefault(name, []).append("<class>")
        methods = {}
        for node in next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == client
        ).body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                methods.setdefault(node.name, []).append(node)
        equal(
            sorted(name for name in methods if name.startswith("paginate_")),
            sorted([*PAGINATORS, *OPERATIONS]),
            label + " paginators",
        )
        for name, operation in PAGINATORS.items():
            what = "%s %s" % (label, name)
            nodes = methods.get(name, [])
            ordinary = methods.get(operation, [])
            if [is_overload(n) for n in nodes] != [True, True, False] or len(
                ordinary
            ) != 3:
                FAILURES.append(what + " is not two overloads and an implementation")
                continue
            # A plain def in both clients: the async one returns an async iterator.
            check(
                all(type(n) is ast.FunctionDef for n in nodes),
                what + " is a coroutine",
            )
            # It takes exactly what the operation's method takes, and, right after
            # plugins, the keyword-only SDK option, which the operation does not take.
            for index in range(3):
                arguments = copy.deepcopy(nodes[index].args)
                names = [a.arg for a in arguments.kwonlyargs]
                option = None
                if "stop_on_same_token" in names:
                    at = names.index("stop_on_same_token")
                    annotation = arguments.kwonlyargs.pop(at).annotation
                    default = arguments.kw_defaults.pop(at)
                    option = (
                        names[at - 1] if at else None,
                        annotation and ast.unparse(annotation),
                        default and ast.unparse(default),
                    )
                equal(
                    option,
                    ("plugins", "bool", "True"),
                    "%s stop_on_same_token of definition %d" % (what, index),
                )
                equal(
                    ast.dump(arguments),
                    ast.dump(ordinary[index].args),
                    "%s operation parameters of definition %d" % (what, index),
                )
                check(
                    "stop_on_same_token"
                    not in [a.arg for a in ordinary[index].args.kwonlyargs],
                    "%s operation definition %d takes stop_on_same_token"
                    % (what, index),
                )
            # Each definition returns the runtime paginator of the page's model and
            # its items. The runtime type's name is bound to nothing else here.
            kind, arguments = RETURNS[name]
            for node in nodes:
                returns = node.returns
                head = returns.value.id if isinstance(returns, ast.Subscript) else None
                written = None
                if head:
                    elements = (
                        returns.slice.elts
                        if isinstance(returns.slice, ast.Tuple)
                        else [returns.slice]
                    )
                    written = ", ".join(ast.unparse(e) for e in elements)
                equal(
                    (imported.get(head), written),
                    ([runtime + kind], arguments),
                    what + " return type",
                )
            docs = ast.get_docstring(nodes[1]) or ""
            check(
                docs.startswith("Iterates the pages of the "),
                "%s keyword overload docs: %r" % (what, docs),
            )
            check(
                "stop_on_same_token:" in docs and "not sent to the service" in docs,
                "%s keyword overload documents no stop_on_same_token: %r"
                % (what, docs),
            )


# --- Importing -----------------------------------------------------------------


LAZY = """
import sys
sys.path.insert(0, sys.argv[1])
import pages
loaded = sorted(n for n in sys.modules if n.startswith("pages."))
assert not loaded, loaded
import pages.client, pages.aio.client
models = sys.modules["pages.models"]
built = sorted(models._registry._classes)
assert not built, built
operations = [n for n in models._operation_names if n in vars(models)]
assert not operations, operations
print("lazy")
"""


def check_lazy():
    # Importing the package loads no client, and importing the clients builds no
    # model class and no operation.
    result = subprocess.run(
        [sys.executable, "-c", LAZY, str(SOURCE)],
        capture_output=True,
        text=True,
        check=False,
    )
    equal(
        (result.returncode, result.stdout.strip()),
        (0, "lazy"),
        "lazy imports: " + result.stderr,
    )


# --- Typing --------------------------------------------------------------------


CONSUMER = """
from collections.abc import AsyncIterator, Iterator
from typing import assert_type

from smithy_core.aio.pagination import AsyncItemPaginator, AsyncPaginator
from smithy_core.pagination import ItemPaginator, Paginator

from pages import AsyncPaginator as AsyncPages, Paginator as Pages
from pages import models as m
from pages.aio.config import Plugin as AsyncPlugin
from pages.config import Plugin


def use(client: Pages, plugin: Plugin) -> None:
    things = client.paginate_list_things(max_results=1, plugins=[plugin])
    assert_type(things, ItemPaginator[m.ListThingsOutput, m.Thing])
    pages: Iterator[m.ListThingsOutput] = things
    for page in pages:
        assert_type(page, m.ListThingsOutput)
    assert_type(things.items(), Iterator[m.Thing])
    request: m.ListThingsInputDict = {"max_results": 1}
    for paginator in (
        client.paginate_list_things(request),
        client.paginate_list_things(**request),
        client.paginate_list_things(m.ListThingsInput()),
        client.paginate_list_things(max_results=1, stop_on_same_token=False),
        client.paginate_list_things(m.ListThingsInput(), stop_on_same_token=False),
        client.paginate_list_things(request, stop_on_same_token=False),
    ):
        assert_type(paginator, ItemPaginator[m.ListThingsOutput, m.Thing])
    assert_type(
        client.paginate_scan_items(plugins__="t", plugins_="p").items(),
        Iterator[tuple[str, m.Plugin | None]],
    )
    assert_type(
        client.paginate_inspect(),
        ItemPaginator[m.InspectOutput, list[m.AsyncItemPaginator] | None],
    )
    assert_type(client.paginate_list_books().items(), Iterator[str])
    assert_type(client.paginate_count(), Paginator[m.CountOutput])
    poll: m.PollInputDict = {"stop_on_same_token__": "t", "stop_on_same_token_": "o"}
    assert_type(
        client.paginate_poll(**poll, stop_on_same_token=False),
        Paginator[m.PollOutput],
    )


async def use_async(client: AsyncPages, plugin: AsyncPlugin) -> None:
    things = client.paginate_list_things(max_results=1, plugins=[plugin])
    assert_type(things, AsyncItemPaginator[m.ListThingsOutput, m.Thing])
    pages: AsyncIterator[m.ListThingsOutput] = things
    async for page in pages:
        assert_type(page, m.ListThingsOutput)
    assert_type(things.items(), AsyncIterator[m.Thing])
    assert_type(
        client.paginate_list_things({"max_results": 1}),
        AsyncItemPaginator[m.ListThingsOutput, m.Thing],
    )
    for paginator in (
        client.paginate_list_things(max_results=1, stop_on_same_token=False),
        client.paginate_list_things(m.ListThingsInput(), stop_on_same_token=False),
        client.paginate_list_things({"max_results": 1}, stop_on_same_token=False),
    ):
        assert_type(paginator, AsyncItemPaginator[m.ListThingsOutput, m.Thing])
    assert_type(
        client.paginate_scan_items(plugins__="t").items(),
        AsyncIterator[tuple[str, m.Plugin | None]],
    )
    assert_type(
        client.paginate_inspect(),
        AsyncItemPaginator[m.InspectOutput, list[m.AsyncItemPaginator] | None],
    )
    assert_type(client.paginate_count(), AsyncPaginator[m.CountOutput])
    assert_type(
        client.paginate_poll(stop_on_same_token__="t", stop_on_same_token=False),
        AsyncPaginator[m.PollOutput],
    )
"""

# Each line marked "expect-error" must be an error, and no other line may be.
MISUSE = """
from pages import AsyncPaginator as AsyncPages, Paginator as Pages
from pages import models as m


def misuse(client: Pages) -> None:
    client.paginate_count().items()  # expect-error
    client.paginate_list_things(max_results="1")  # expect-error
    client.paginate_list_things(plugins=[1])  # expect-error
    client.paginate_list_things(m.ListThingsInput(), max_results=1)  # expect-error
    client.paginate_list_things(stop_on_same_token="no")  # expect-error
    client.paginate_ordinary()  # expect-error


async def misuse_async(client: AsyncPages) -> None:
    await client.paginate_list_things()  # expect-error
    client.paginate_count().items()  # expect-error
    client.paginate_ordinary()  # expect-error


def untyped(value) -> None: ...  # expect-error
"""


def check_typing():
    # Pyright reads the generated project's strict configuration. The untyped
    # function is an error only under it.
    files = {"pagination_consumer.py": CONSUMER, "pagination_misuse.py": MISUSE}
    for name, source in files.items():
        (SOURCE / name).write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--outputjson",
            *("src/" + name for name in files),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        report = json.loads(result.stdout)
    except ValueError:
        FAILURES.append(
            "pyright did not report: %s %s" % (result.stdout, result.stderr)
        )
        return
    print("pyright", report.get("version"), report["summary"])
    equal(report["summary"]["filesAnalyzed"], len(files), "files pyright analyzed")
    errors = {name: set() for name in files}
    for diagnostic in report["generalDiagnostics"]:
        if diagnostic["severity"] == "error":
            name = Path(diagnostic["file"]).name
            errors.setdefault(name, set()).add(diagnostic["range"]["start"]["line"])
            print(
                "  %s:%d %s"
                % (
                    name,
                    diagnostic["range"]["start"]["line"] + 1,
                    diagnostic["message"],
                )
            )
    expected = {
        name: {
            number
            for number, line in enumerate(textwrap.dedent(source).lstrip().splitlines())
            if line.endswith("# expect-error")
        }
        for name, source in files.items()
    }
    equal(errors, expected, "lines with type errors")


# --- Behavior ------------------------------------------------------------------


class Transport:
    """Answers each request with the next response body, and fails past the last."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, *bodies):
        self.bodies = [json.dumps(body).encode() for body in bodies]
        self.requests = []

    def __deepcopy__(self, memo):
        return self

    def _respond(self, request, body):
        if not self.bodies:
            raise AssertionError("unexpected request %d" % (len(self.requests) + 1))
        destination = request.destination
        self.requests.append(
            (
                destination.path,
                dict(parse_qsl(destination.query or "")),
                json.loads(body) if body else None,
            )
        )
        fields = tuples_to_fields([("Content-Type", "application/json")])
        return HTTPResponse(status=200, fields=fields, body=self.bodies.pop(0))

    def send(self, request, *, request_config=None):
        body = request.body
        if hasattr(body, "read"):
            body = body.read()
        return self._respond(request, bytes(body or b""))


class AsyncTransport(Transport):
    async def send(self, request, *, request_config=None):
        body = request.body
        if hasattr(body, "read"):
            body = body.read()
            if inspect.isawaitable(body):
                body = await body
        response = self._respond(request, bytes(body or b""))
        response.body = AsyncBytesReader(response.body)
        return response


def make(transport, plugins=None):
    import pages

    aio = isinstance(transport, AsyncTransport)
    config = pages.AsyncConfig if aio else pages.Config
    client = pages.AsyncPaginator if aio else pages.Paginator
    return client(
        config(
            endpoint_uri="https://example.com",
            transport=transport,
            retry_strategy=SimpleRetryStrategy(max_attempts=1),
        ),
        plugins=plugins,
    )


def both(test):
    """Runs a check with a sync client, then with an async one. The check gets a
    function that collects an iterator of either kind."""

    def collect_sync(iterator):
        return list(iterator)

    test(Transport, collect_sync)

    def collect_async(iterator):
        async def drain():
            return [value async for value in iterator]

        return LOOP.run_until_complete(drain())

    test(AsyncTransport, collect_async)


LOOP = asyncio.new_event_loop()


def check_pages():
    # Each page is one call of the ordinary operation, sent as iteration reaches
    # it. The caller's token starts the first page; an empty page with a token
    # continues; a page without one ends.
    def test(transport_type, collect):
        transport = transport_type(
            {"things": [{"name": "a"}], "nextToken": "t1"},
            {"things": [], "nextToken": "t2"},
            {"things": [{"name": "c"}]},
        )
        pages = make(transport).paginate_list_things(max_results=2, next_token="t0")
        what = transport_type.__name__
        check(not inspect.isawaitable(pages), what + " paginator is awaitable")
        equal(transport.requests, [], what + " requests before iteration")
        equal(
            [
                (type(p).__name__, [t.name for t in p.things], p.next_token)
                for p in collect(pages)
            ],
            [
                ("ListThingsOutput", ["a"], "t1"),
                ("ListThingsOutput", [], "t2"),
                ("ListThingsOutput", ["c"], None),
            ],
            what + " pages",
        )
        equal(
            transport.requests,
            [
                ("/things", {}, {"maxResults": 2, "nextToken": "t0"}),
                ("/things", {}, {"maxResults": 2, "nextToken": "t1"}),
                ("/things", {}, {"maxResults": 2, "nextToken": "t2"}),
            ],
            what + " requests",
        )

        # Its items are the things of each page.
        transport = transport_type(
            {"things": [{"name": "a"}], "nextToken": "t1"}, {"things": [{"name": "b"}]}
        )
        items = make(transport).paginate_list_things().items()
        equal([t.name for t in collect(items)], ["a", "b"], what + " items")

    both(test)


def check_inputs():
    import pages.models as m

    # A model, a dictionary, or keyword arguments, as for the operation. The
    # caller's request is not changed.
    model = m.ListThingsInput(max_results=1, next_token="a")
    request = {"max_results": 1, "next_token": "a"}
    for label, args, kwargs in (
        ("model", (model,), {}),
        ("dictionary", (request,), {}),
        ("keywords", (), request),
    ):
        transport = Transport({"nextToken": "b"}, {})
        list(make(transport).paginate_list_things(*args, **kwargs))
        equal(
            [body for _, _, body in transport.requests],
            [{"maxResults": 1, "nextToken": "a"}, {"maxResults": 1, "nextToken": "b"}],
            label + " requests",
        )
    equal(
        (model.next_token, request),
        ("a", {"max_results": 1, "next_token": "a"}),
        "caller's request",
    )

    # A request the operation would reject is rejected at once, before anything
    # is sent.
    transport = Transport()
    client = make(transport)
    for args, kwargs in (
        ((model,), {"max_results": 1}),
        ((1,), {}),
        ((model, model), {}),
    ):
        try:
            client.paginate_list_things(*args, **kwargs)
        except TypeError:
            continue
        FAILURES.append("paginate_list_things%r accepted %r" % (args, kwargs))
    equal(transport.requests, [], "requests of rejected calls")


def check_paths():
    # ScanItems names its input token "plugins", whose Python name is escaped past
    # its sibling's, and reaches its token and items through a structure and a
    # member whose Python name is escaped. Its items are a sparse map's entries.
    def test(transport_type, collect):
        what = transport_type.__name__
        transport = transport_type(
            {"page": {"nextToken": "n1", "class": {"k": {"name": "x"}, "n": None}}},
            {"page": {"nextToken": "n2", "class": {}}},
            {"page": {"class": {"z": {"name": "y"}}}},
        )
        items = make(transport).paginate_scan_items(
            plugins__="t0", plugins_="other", max_results=3
        )
        equal(
            [(key, value and value.name) for key, value in collect(items.items())],
            [("k", "x"), ("n", None), ("z", "y")],
            what + " scan items",
        )
        equal(
            [body for _, _, body in transport.requests],
            [
                {"plugins": token, "plugins_": "other", "maxResults": 3}
                for token in ("t0", "n1", "n2")
            ],
            what + " scan requests",
        )

        # A missing structure on the path means no token and no items.
        transport = transport_type({})
        equal(
            collect(make(transport).paginate_scan_items().items()),
            [],
            what + " items without a page",
        )
        equal(len(transport.requests), 1, what + " requests without a page")

        # Each item of Inspect is a list, or None.
        transport = transport_type(
            {"rows": [[{"name": "a"}], None, []], "nextToken": "r1"},
            {"rows": [[{"name": "b"}]]},
        )
        rows = collect(make(transport).paginate_inspect().items())
        equal(
            [row and [(type(t).__name__, t.name) for t in row] for row in rows],
            [[("AsyncItemPaginator", "a")], None, [], [("AsyncItemPaginator", "b")]],
            what + " rows",
        )

        # ListBooks belongs to a resource, overrides only the output token, and
        # sends its token in the query.
        transport = transport_type(
            {"titles": ["a"], "nextPage": "b1"}, {"titles": ["b"]}
        )
        titles = (
            make(transport).paginate_list_books(next_token="b0", max_results=5).items()
        )
        equal(collect(titles), ["a", "b"], what + " titles")
        equal(
            [(path, query) for path, query, _ in transport.requests],
            [
                ("/books", {"nextToken": "b0", "maxResults": "5"}),
                ("/books", {"nextToken": "b1", "maxResults": "5"}),
            ],
            what + " book requests",
        )

        # Count has no items, so its paginator iterates only pages.
        transport = transport_type({"nextToken": "c1", "total": 1}, {"total": 2})
        count = make(transport).paginate_count()
        expected = AsyncPaginator if transport_type is AsyncTransport else Paginator
        check(
            type(count) is expected and not hasattr(count, "items"),
            "%s count paginator is a %r" % (what, type(count)),
        )
        equal([page.total for page in collect(count)], [1, 2], what + " counts")
        kind = AsyncItemPaginator if transport_type is AsyncTransport else ItemPaginator
        check(
            isinstance(make(transport).paginate_list_things(), kind),
            what + " item paginator type",
        )

        # Ordinary has the members but not the trait.
        check(
            not hasattr(make(transport), "paginate_ordinary"),
            what + " paginates Ordinary",
        )

        # Upload has the trait, but its streaming input can't be sent again.
        client = make(transport)
        check(
            hasattr(client, "upload") and not hasattr(client, "paginate_upload"),
            what + " paginates Upload",
        )

    both(test)


def check_names():
    # Operation methods keep their names; each paginator iterates its own operation.
    def test(transport_type, collect):
        what = transport_type.__name__
        transport = transport_type({"nextToken": "x"})
        client = make(transport)
        output = client.paginate_foo()
        if inspect.isawaitable(output):
            output = LOOP.run_until_complete(output)
        equal(
            (type(output).__name__, [path for path, _, _ in transport.requests]),
            ("PaginateFooOutput", ["/paginate-foo"]),
            what + " paginate_foo",
        )
        check(type(client).close.__module__.startswith("smithy_core."), what + " close")
        for name, output, path in (
            ("paginate_foo_", "FooOutput", "/foo"),
            ("paginate_paginate_foo", "PaginateFooOutput", "/paginate-foo"),
            ("paginate_close_", "CloseOutput", "/close"),
        ):
            transport = transport_type({"nextToken": "n"}, {})
            pages = collect(getattr(make(transport), name)())
            equal(
                (
                    [type(page).__name__ for page in pages],
                    [p for p, _, _ in transport.requests],
                ),
                ([output, output], [path, path]),
                "%s %s" % (what, name),
            )

    both(test)


def check_plugins():
    # The paginator does nothing until it is iterated. Then the client is set up
    # once, with its plugins, and each page is requested through the operation's
    # method, with the caller's plugins applied to that call's own config.
    def test(transport_type, collect):
        what = transport_type.__name__
        transport = transport_type({"nextToken": "t1"}, {}, {"nextToken": "ignored"})
        setups, calls = [], []
        client = make(transport, plugins=[setups.append])
        pages = client.paginate_list_things(plugins=[calls.append])
        equal(
            (client._setup_done, setups, calls, transport.requests),
            (False, [], [], []),
            what + " state before iteration",
        )
        equal(len(collect(pages)), 2, what + " pages")
        equal(
            (len(setups), len(calls), len(transport.requests)),
            (1, 2, 2),
            what + " calls",
        )
        check(
            calls[0] is not calls[1] and all(c is not setups[0] for c in calls),
            what + " shares a config",
        )

        # The operation's method still requests one page.
        output = client.list_things(next_token="x")
        if inspect.isawaitable(output):
            output = LOOP.run_until_complete(output)
        equal(
            (output.next_token, len(transport.requests)),
            ("ignored", 3),
            what + " one call",
        )

    both(test)


def check_stop_on_same_token():
    import pages.models as m

    # stop_on_same_token=False keeps paging when a response repeats the request's
    # token, the caller's starting one or a later one, for each form of request.
    # Only an absent token ends it, and the option is never sent.
    def test(transport_type, collect):
        what = transport_type.__name__
        for label, args, kwargs in (
            ("keywords", (), {"max_results": 1, "next_token": "t0"}),
            ("model", (m.ListThingsInput(max_results=1, next_token="t0"),), {}),
            ("dictionary", ({"max_results": 1, "next_token": "t0"},), {}),
        ):
            name = "%s %s stop_on_same_token=False" % (what, label)
            transport = transport_type(
                {"things": [{"name": "a"}], "nextToken": "t0"},
                {"things": [{"name": "b"}], "nextToken": "t1"},
                {"things": [], "nextToken": "t1"},
                {"things": [{"name": "c"}]},
            )
            try:
                pages = make(transport).paginate_list_things(
                    *args, stop_on_same_token=False, **kwargs
                )
                check(not inspect.isawaitable(pages), name + " is awaitable")
                equal(transport.requests, [], name + " requests before iteration")
                equal(
                    [
                        ([t.name for t in p.things], p.next_token)
                        for p in collect(pages)
                    ],
                    [(["a"], "t0"), (["b"], "t1"), ([], "t1"), (["c"], None)],
                    name + " pages",
                )
            except Exception as error:  # noqa: BLE001 - reported per form
                FAILURES.append("%s raised %r" % (name, error))
                continue
            equal(
                transport.requests,
                [
                    ("/things", {}, {"maxResults": 1, "nextToken": token})
                    for token in ("t0", "t0", "t1", "t1")
                ],
                name + " requests",
            )

    both(test)


def check_option_collision():
    import pages.models as m

    # Poll's input token, stopOnSameToken, is escaped past the SDK option and its
    # sibling stop_on_same_token_, in the model and in its dictionary form (typed
    # in the stub, so checked by the consumer and below), and is still sent under
    # its own wire name, beside the option, which is not.
    names = {f.name for f in dataclasses.fields(m.PollInput)}
    equal(
        sorted(n for n in names if n.startswith("stop_on_same_token")),
        ["stop_on_same_token_", "stop_on_same_token__"],
        "Poll input fields",
    )

    def test(transport_type, collect):
        what = transport_type.__name__
        request = {"stop_on_same_token__": "p0", "stop_on_same_token_": "o"}
        for label, args, kwargs in (
            ("keywords", lambda: (), request),
            ("model", lambda: (m.PollInput(**request),), {}),
            ("dictionary", lambda: (request,), {}),
        ):
            name = "%s poll %s" % (what, label)
            transport = transport_type(
                {"nextToken": "p0"}, {"nextToken": "p1"}, {"nextToken": "p1"}, {}
            )
            try:
                pages = make(transport).paginate_poll(
                    *args(), stop_on_same_token=False, **kwargs
                )
                equal(
                    [p.next_token for p in collect(pages)],
                    ["p0", "p1", "p1", None],
                    name + " pages",
                )
            except Exception as error:  # noqa: BLE001 - reported per form
                FAILURES.append("%s raised %r" % (name, error))
                continue
            equal(
                [body for _, _, body in transport.requests],
                [
                    {"stopOnSameToken": token, "stop_on_same_token_": "o"}
                    for token in ("p0", "p0", "p1", "p1")
                ],
                name + " requests",
            )

        # The operation's method sends the escaped member once, as its wire name.
        transport = transport_type({"nextToken": "ignored"})
        try:
            output = make(transport).poll(stop_on_same_token__="x")
            if inspect.isawaitable(output):
                output = LOOP.run_until_complete(output)
        except Exception as error:  # noqa: BLE001 - reported with the rest
            FAILURES.append("%s poll raised %r" % (what, error))
            return
        equal(
            (output.next_token, [body for _, _, body in transport.requests]),
            ("ignored", [{"stopOnSameToken": "x"}]),
            what + " poll",
        )

    both(test)


def main():
    print("python %s, smithy_core %s" % (sys.executable, smithy_core.__file__))
    checks = [
        check_definitions,
        check_lazy,
        check_typing,
        check_pages,
        check_inputs,
        check_paths,
        check_names,
        check_plugins,
        check_stop_on_same_token,
        check_option_collision,
    ]
    for run in checks:
        try:
            run()
        except Exception as error:  # noqa: BLE001 - reported with the rest
            FAILURES.append("%s raised %r" % (run.__name__, error))
    if FAILURES:
        print("%d pagination checks failed:\n" % len(FAILURES))
        print("\n\n".join(FAILURES))
        sys.exit(1)
    print("pagination checks passed")


if __name__ == "__main__":
    main()
