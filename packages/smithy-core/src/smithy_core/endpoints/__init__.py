# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from ._resolver import BddEndpointResolver, StaticEndpointResolver, resolve_static_uri
from ._types import (
    ENDPOINT_HEADERS,
    ENDPOINT_PARAMETERS,
    RESOLVED_ENDPOINT,
    STATIC_ENDPOINT_CONFIG,
    BuiltinBinding,
    BuiltinGetter,
    Endpoint,
    EndpointAuthScheme,
    EndpointAuthSchemeFactory,
    EndpointBdd,
    EndpointResolverParams,
    RulesExtension,
    StaticEndpointConfig,
)

__all__ = [
    "ENDPOINT_HEADERS",
    "ENDPOINT_PARAMETERS",
    "RESOLVED_ENDPOINT",
    "STATIC_ENDPOINT_CONFIG",
    "BddEndpointResolver",
    "BuiltinBinding",
    "BuiltinGetter",
    "Endpoint",
    "EndpointAuthScheme",
    "EndpointAuthSchemeFactory",
    "EndpointBdd",
    "EndpointResolverParams",
    "RulesExtension",
    "StaticEndpointConfig",
    "StaticEndpointResolver",
    "resolve_static_uri",
]
