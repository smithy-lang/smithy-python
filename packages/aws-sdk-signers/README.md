## AWS SDK Signers for Python

AWS SDK Signers for Python provides stand-alone signing functionality. This enables users to
create standardized request signatures (currently only SigV4) and apply them to
common HTTP utilities like AIOHTTP, Curl, Postman, Requests and urllib3.

This project is currently in an **Alpha** phase of development. There likely
will be breakages and redesigns between minor patch versions as we collect
user feedback. We strongly recommend pinning to a minor version and reviewing
the changelog carefully before upgrading.

## Getting Started

Currently, the `aws-sdk-signers` module provides two high level signers,
`AsyncSigV4Signer` and `SigV4Signer`.

Both of these signers takes three inputs to their primary `sign` method.

* A [**SigV4SigningProperties**](https://github.com/smithy-lang/smithy-python/blob/3d205be8ece1c5f4c992a29ce9757c5562e59322/packages/aws-sdk-signers/src/aws_sdk_signers/signers.py#L43-L49) object defining:
  * The service for the request,
  * The intended AWS region (e.g. us-west-2),
  * An optional date that will be auto-populated with the current time if not supplied,
  * An optional boolean, payload_signing_enabled to toggle payload signing. True by default.
  * An optional boolean, content_checksum_enabled, to include the x-amz-content-sha256 header. True by default.
  * An optional boolean, uri_encode_path, to toggle double-encoding the URI path. True by default.
* An [**AWSRequest**](https://github.com/smithy-lang/smithy-python/blob/3d205be8ece1c5f4c992a29ce9757c5562e59322/packages/aws-sdk-signers/src/aws_sdk_signers/_http.py#L335), similar to the [AWSRequest object](https://github.com/boto/botocore/blob/7d197f9e1fe903ba3badee62a1ecac916ba2cfb5/botocore/awsrequest.py#L433) from boto3 or the [Request object](https://requests.readthedocs.io/en/latest/api/#requests.Request) from Requests.
* An [**AWSCredentialIdentity**](https://github.com/smithy-lang/smithy-python/blob/3d205be8ece1c5f4c992a29ce9757c5562e59322/packages/aws-sdk-signers/src/aws_sdk_signers/_identity.py#L11), a dataclass holding standard AWS credential information.

## License

This project is licensed under the Apache-2.0 License.
