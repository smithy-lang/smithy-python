# Example Signers for aws-sdk-signers

## Requests
We utilize the `AuthBase` construct provided by Requests to apply our signature
to each request. Our `SigV4Auth` class takes two arguments
[`SigV4SigningProperties`](https://github.com/smithy-lang/smithy-python/blob/9c0225b2810b3f68a84aa074e9b4e728a3043721/packages/aws-sdk-signers/src/aws_sdk_signers/signers.py#L44-L50)
and an [`AWSCredentialIdentity`](https://github.com/smithy-lang/smithy-python/blob/9c0225b2810b3f68a84aa074e9b4e728a3043721/packages/aws-sdk-signers/src/aws_sdk_signers/_identity.py#L10-L15).
These will be used across requests as "immutable" input. This is currently an
intentional design decision to work with Requests auth design. We'd love to
hear feedback on how you feel about the current approach, we recommend checking
the AIOHTTP section below for an alternative design.

### Requests Sample
```python
from os import environ

import requests

from examples import requests_signer
from aws_sdk_signers import SigV4SigningProperties, AWSCredentialIdentity

SERVICE="lambda"
REGION="us-west-2"

# A GET request to this URL performs a "ListFunctions" invocation.
# Full API documentation can be found here:
# https://docs.aws.amazon.com/lambda/latest/api/API_ListFunctions.html
URL='https://lambda.us-west-2.amazonaws.com/2015-03-31/functions/'

def get_credentials_from_env():
    """You will need to pull credentials from some source to use the signer.
    This will auto-populate an AWSCredentialIdentity when credentials are
    available through the env.

    You may also consider using another SDK to assume a role or pull
    credentials from another source.
    """
    return AWSCredentialIdentity(
        access_key_id=environ["AWS_ACCESS_KEY_ID"],
        secret_access_key=environ["AWS_SECRET_ACCESS_KEY"],
        session_token=environ.get("AWS_SESSION_TOKEN"),
    )

# Set up our properties and identity
identity = get_credentials_from_env()
properties = SigV4SigningProperties(region=REGION, service=SERVICE)

# Configure the auth class for signing
sigv4_auth = requests_signer.SigV4Auth(properties, identity)

r = requests.get(URL, auth=sigv4_auth)
```

## AIOHTTP
For AIOHTTP, we don't have a concept of a Request object, or option to subclass an
existing auth mechanism. Instead, we'll take parameters you normally pass to a Session
method and use them to generate signing headers before passing them on to AIOHTTP.

This signer will be configured the same way as Requests and provides an Async signing
interface to be used alongside AIOHTTP. This is still a work in progress and will likely
have some amount of iteration to improve performance and ergonomics as we collect feedback.

### AIOHTTP Sample
```python
import asyncio
from collections.abc import AsyncIterable, Mapping
from os import environ

import aiohttp

from examples import aiohttp_signer
from aws_sdk_signers import SigV4SigningProperties, AWSCredentialIdentity


SERVICE="lambda"
REGION="us-west-2"

# A GET request to this URL performs a "ListFunctions" invocation.
# Full API documentation can be found here:
# https://docs.aws.amazon.com/lambda/latest/api/API_ListFunctions.html
URL='https://lambda.us-west-2.amazonaws.com/2015-03-31/functions/'

def get_credentials_from_env():
    """You will need to pull credentials from some source to use the signer.
    This will auto-populate an AWSCredentialIdentity when credentials are
    available through the env.

    You may also consider using another SDK to assume a role or pull
    credentials from another source.
    """
    return AWSCredentialIdentity(
        access_key_id=environ["AWS_ACCESS_KEY_ID"],
        secret_access_key=environ["AWS_SECRET_ACCESS_KEY"],
        session_token=environ.get("AWS_SESSION_TOKEN"),
    )

# Set up our signing_properties and identity
identity = get_credentials_from_env()
properties = SigV4SigningProperties(region=REGION, service=SERVICE)

signer = aiohttp_signer.SigV4Signer(properties, identity)

async def make_request(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: AsyncIterable[bytes] | None,
) -> None:
    # For more robust applications, you'll likely want to reuse this session.
    async with aiohttp.ClientSession() as session:
        signing_headers = await signer.generate_signature(method, url, headers, body)
        headers.update(signing_headers)
        async with session.request(method, url, headers=headers, data=body) as response:
            print("Status:", response.status)
            print("Content-Type:", response.headers['content-type'])

            body_content = await response.text()
            print(body_content)

asyncio.run(make_request("GET", URL, {}, None))
```

## Curl Signer
For curl, we're generating a string to be used in a terminal or invoked subprocess.
This currently only supports known arguments like defining the method, headers,
and a request body. We can expand this to support arbitrary curl arguments in
a future version if there's demand.

### Curl Sample
```python
from examples import curl_signer
from aws_sdk_signers import SigV4SigningProperties, AWSCredentialIdentity

from os import environ


SERVICE="lambda"
REGION="us-west-2"

# A GET request to this URL performs a "ListFunctions" invocation.
# Full API documentation can be found here:
# https://docs.aws.amazon.com/lambda/latest/api/API_ListFunctions.html
URL='https://lambda.us-west-2.amazonaws.com/2015-03-31/functions/'


properties = SigV4SigningProperties(region=REGION, service=SERVICE)
identity = AWSCredentialIdentity(
    access_key_id=environ["AWS_ACCESS_KEY_ID"],
    secret_access_key=environ["AWS_SECRET_ACCESS_KEY"],
    session_token=environ["AWS_SESSION_TOKEN"]
)

# Our curl signer doesn't need state so we
# can call classmethods directly on the signer.
signer = curl_signer.SigV4Curl
curl_cmd = signer.generate_signed_curl_cmd(
    properties=properties,
    identity=identity,
    method="GET",
    url=URL,
    headers={},
    body=None,
)
print(curl_cmd)
```
