#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import importlib.metadata

__version__: str = importlib.metadata.version("smithy-aws-core")


from smithy_core.types import PropertyKey


REGION = PropertyKey(key="region", value_type=str)
"""An AWS region."""
