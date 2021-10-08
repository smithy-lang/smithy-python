from smithy_python._private.http import Request, URL, Response


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
