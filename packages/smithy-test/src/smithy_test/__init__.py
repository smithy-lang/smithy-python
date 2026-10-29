#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from ._endpoints import check_rules_case as check_rules_case
from ._private.conformance import ConformanceError as ConformanceError
from ._private.conformance import verify_models as verify_models
from ._private.equality import deep_equal as deep_equal
from ._private.equality import xml_equal as xml_equal

__version__ = "0.1.0"
__all__ = (
    "ConformanceError",
    "check_rules_case",
    "deep_equal",
    "verify_models",
    "xml_equal",
)
