# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


from typing import List, Tuple, Optional, Any
from smithy_python.interfaces import http as http_interface


HeadersList = List[Tuple[str, str]]
QueryParamsList = List[Tuple[str, str]]


class URL:
    def __init__(
        self,
        hostname: str,
        path: Optional[str] = None,
        scheme: Optional[str] = None,
        query_params: Optional[QueryParamsList] = None,
        port: Optional[int] = None,
    ):
        self.hostname: str = hostname
        self.port: Optional[int] = port

        self.path: str = ""
        if path is not None:
            self.path = path

        self.scheme: str = "https"
        if scheme is not None:
            self.scheme = scheme

        self.query_params: QueryParamsList = []
        if query_params is not None:
            self.query_params = query_params


class Request:
    def __init__(
        self,
        url: http_interface.URL,
        method: str = "GET",
        headers: Optional[HeadersList] = None,
        body: Any = None,
    ):
        self.url: http_interface.URL = url
        self.method: str = method
        self.body: Any = body

        self.headers: HeadersList = []
        if headers is not None:
            self.headers = headers


class Response:
    def __init__(
        self,
        status_code: int,
        headers: HeadersList,
        body: Any,
    ):
        self.status_code: int = status_code
        self.headers: HeadersList = headers
        self.body: Any = body
