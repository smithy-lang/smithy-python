#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# Reserves the "smithy_aws_core.identity.chain_providers" entry-point group for
# sync providers; the async chain discovers under "...aio.identity.chain_providers".
# TODO(sync-api): populate alongside the sync credential chain.
__all__: list[str] = []
