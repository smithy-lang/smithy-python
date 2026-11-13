#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from ._endpoints import check_rules_case as check_rules_case
from ._private.conformance import ConformanceError as ConformanceError
from ._private.conformance import verify_models as verify_models
from ._private.equality import deep_equal as deep_equal
from ._private.equality import xml_equal as xml_equal
from .http_mock import HTTPMockController as HTTPMockController
from .http_mock import HTTPMockError as HTTPMockError
from .http_mock import HTTPMockExpectation as HTTPMockExpectation
from .http_mock import HTTPMockMismatchError as HTTPMockMismatchError
from .http_mock import mock as mock

__version__ = "0.4.0"
__all__ = (
    "ConformanceError",
    "HTTPMockController",
    "HTTPMockError",
    "HTTPMockExpectation",
    "HTTPMockMismatchError",
    "check_rules_case",
    "deep_equal",
    "mock",
    "verify_models",
    "xml_equal",
)
