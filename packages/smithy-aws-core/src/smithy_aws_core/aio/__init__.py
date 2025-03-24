#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.shapes import ShapeID
from smithy_http.aio.interfaces import ErrorExtractor, HTTPResponse


class AmznErrorExtractor(ErrorExtractor):
    """Attempts to extract the Amazon-specific 'X-Amzn-Errortype' error header from a
    response."""

    def get_error(self, response: HTTPResponse):
        if "x-amzn-errortype" in response.fields:
            val = response.fields["x-amzn-errortype"].values[0]
            return ShapeID(val)
