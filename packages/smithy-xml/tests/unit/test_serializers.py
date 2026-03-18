# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest
from smithy_xml import XMLCodec


def test_create_serializer_raises() -> None:
    with pytest.raises(NotImplementedError, match="XML serialization is not supported"):
        XMLCodec().create_serializer(BytesIO())
