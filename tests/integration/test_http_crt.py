import pytest

from smithy_python._private.http import Request, URL
from smithy_python._private.http.crt import (
    AwsCrtHttpSessionConfig,
    SyncAwsCrtHttpSession,
    AsyncAwsCrtHttpSession,
)


@pytest.fixture  # type: ignore
def aws_request() -> Request:
    return Request(
        url=URL(hostname="aws.amazon.com"),
        headers=[("host", "aws.amazon.com"), ("user-agent", "smithy-python-test")],
    )


def test_basic_request(aws_request: Request) -> None:
    config = AwsCrtHttpSessionConfig(force_http_2=True)
    session = SyncAwsCrtHttpSession(config=config)
    response = session.send(aws_request)
    assert response.status_code == 200
    body = response.body.consume_body()
    assert b"aws" in body
    assert response.body.done


@pytest.mark.asyncio  # type: ignore
async def test_async_basic_request(aws_request: Request) -> None:
    config = AwsCrtHttpSessionConfig(force_http_2=True)
    session = AsyncAwsCrtHttpSession(config=config)
    response = await session.send(aws_request)
    assert response.status_code == 200
    body = await response.body.consume_body()
    assert b"aws" in body
    assert await response.body.done
