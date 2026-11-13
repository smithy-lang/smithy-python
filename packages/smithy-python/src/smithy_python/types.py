# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Generation of complete standalone types packages."""

from __future__ import annotations

from . import _package
from . import generation as _generation
from . import models as _models
from . import schemas as _schemas

__all__ = ["TypesGenerator"]


class TypesGenerator:
    """Generate a standalone package containing schemas and lazy models."""

    def generate(
        self, context: _generation.GenerationContext[_generation.TypesSettings]
    ) -> None:
        """Register every file and dependency in the generation context."""
        _schemas.SchemaGenerator().generate(context)
        _models.ModelGenerator().generate(context)
        package = context.settings.package
        _package.write_package(
            context,
            title=f"{package} Types Package",
            description=context.settings.package_description
            or f"{package} types package",
        )
