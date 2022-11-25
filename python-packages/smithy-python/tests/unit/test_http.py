from smithy_python._private.http import (
    URL,
    Request,
    Response,
    StaticEndpointParams,
    StaticEndpointResolver,
)


def test_url() -> None:
    url = URL(
        hostname="test.com",
        path="/my/path",
        scheme="http",
        query_params=[("foo", "bar")],
        port=80,
    )

    assert url.hostname == "test.com"
    assert url.path == "/my/path"
    assert url.scheme == "http"
    assert url.query_params == [("foo", "bar")]
    assert url.port == 80


def test_request() -> None:
    url = URL(hostname="test.com")
    request = Request(
        url=url,
        headers=[("foo", "bar")],
        body=b"test body",
    )

    assert request.method == "GET"
    assert request.url == url
    assert request.headers == [("foo", "bar")]
    assert request.body == b"test body"


def test_resposne() -> None:
    response = Response(
        status_code=200,
        headers=[("foo", "bar")],
        body=b"test body",
    )

    assert response.status_code == 200
    assert response.headers == [("foo", "bar")]
    assert response.body == b"test body"


async def test_endpoint_provider_with_url_string() -> None:
    params = StaticEndpointParams(
        url="https://foo.example.com/spam:8080?foo=bar&foo=baz"
    )
    expected = URL(
        hostname="foo.example.com",
        path="/spam",
        scheme="https",
        query_params=[("foo", "bar"), ("foo", "baz")],
        port=8080,
    )
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.url == expected
    assert result.headers == []


async def test_endpoint_provider_with_url_object() -> None:
    expected = URL(
        hostname="foo.example.com",
        path="/spam",
        scheme="https",
        query_params=[("foo", "bar"), ("foo", "baz")],
        port=8080,
    )
    params = StaticEndpointParams(url=expected)
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.url == expected
    assert result.headers == []
