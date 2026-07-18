# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Python-native Smithy code generation."""

from .exceptions import CodegenError, ModelError, PluginError
from .filters import AllShapes, ConnectedShapeFilter, ShapeFilter
from .generator import PythonCodeGenerator
from .model import Member, Model, Shape, ShapeID, ShapeType
from .plugins import CodeSection, GeneratorPlugin, PluginRegistry, ProtocolGenerator
from .settings import ArtifactType, GeneratorSettings, PluginEnvironment
from .symbols import (
    PythonDependency,
    PythonSymbolProvider,
    Symbol,
    SymbolProperty,
    SymbolProvider,
)

__all__ = (
    "AllShapes",
    "ArtifactType",
    "CodeSection",
    "CodegenError",
    "ConnectedShapeFilter",
    "GeneratorPlugin",
    "GeneratorSettings",
    "Member",
    "Model",
    "ModelError",
    "PluginEnvironment",
    "PluginError",
    "PluginRegistry",
    "ProtocolGenerator",
    "PythonCodeGenerator",
    "PythonDependency",
    "PythonSymbolProvider",
    "Shape",
    "ShapeFilter",
    "ShapeID",
    "ShapeType",
    "Symbol",
    "SymbolProperty",
    "SymbolProvider",
)

__version__ = "0.1.0"
