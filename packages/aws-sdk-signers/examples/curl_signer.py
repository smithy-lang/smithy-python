"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0

Sample signer using Requests.
"""

import typing
from collections.abc import Iterable, Mapping
from urllib.parse import urlparse

from aws_sdk_signers import AWSRequest, Field, Fields, SigV4Signer, URI

if typing.TYPE_CHECKING:
    from aws_sdk_signers import AWSCredentialIdentity, SigV4SigningProperties


class SigV4Curl:
    """Generates a curl command with a SigV4 signature applied."""

    signer = SigV4Signer()

    @classmethod
    def generate_signed_curl_cmd(
        cls,
        properties: "SigV4SigningProperties",
        identity: "AWSCredentialIdentity",
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Iterable[bytes] | None,
    ) -> str:
        url_parts = urlparse(url)
        uri = URI(
            scheme=url_parts.scheme,
            host=url_parts.hostname,
            port=url_parts.port,
            path=url_parts.path,
            query=url_parts.query,
            fragment=url_parts.fragment,
        )
        fields = Fields([Field(name=k, values=[v]) for k, v in headers.items()])
        awsrequest = AWSRequest(
            destination=uri,
            method=method,
            body=body,
            fields=fields,
        )
        signed_request = cls.signer.sign(
            properties=properties,
            request=awsrequest,
            identity=identity,
        )
        return cls._construct_curl_cmd(request=signed_request)

    @classmethod
    def _construct_curl_cmd(self, request: AWSRequest) -> str:
        cmd_list = ["curl"]
        cmd_list.append(f"-X {request.method.upper()}")
        for header in request.fields:
            cmd_list.append(f'-H "{header.name}: {header.as_string()}"')
        if request.body is not None:
            # Forcing bytes to a utf-8 string, if we need arbitrary bytes for the
            # terminal we should add an option to write to file and use that
            # in the command.
            cmd_list.append(f"-d {b''.join(list(request.body)).decode()}")
        cmd_list.append(request.destination.build())
        return " ".join(cmd_list)
