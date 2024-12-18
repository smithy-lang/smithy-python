from copy import deepcopy

from smithy_http.aio.crt import AWSCRTHTTPClient


def test_deepcopy_client() -> None:
    client = AWSCRTHTTPClient()
    deepcopy(client)
