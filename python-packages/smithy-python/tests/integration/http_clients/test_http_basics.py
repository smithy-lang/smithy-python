# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json
import urllib.request

# mypy: allow-untyped-defs
# mypy: allow-incomplete-defs


def test_uses_local_integ_test_server(running_server) -> None:
    port = running_server
    url = f"http://localhost:{port}"
    with urllib.request.urlopen(url) as f:
        resp = f.read().decode("utf-8")
    resp_json = json.loads(resp)
    assert resp_json["request_headers"]["User-Agent"] == "Python-urllib/3.11"
