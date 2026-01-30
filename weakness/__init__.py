"""Weakness-targeted generation for detection system analysis."""

from synpii.weakness.targeted import WeaknessTargetedGenerator
from synpii.weakness.strategies import (
    BaseWeaknessStrategy,
    OverlapConflictStrategy,
    FormatVariationStrategy,
    ContextDependencyStrategy,
    CoverageGapStrategy,
    EntityConfusionStrategy,
)
from synpii.weakness.types import WeaknessType, WeaknessReport

__all__ = [
    "WeaknessTargetedGenerator",
    "BaseWeaknessStrategy",
    "OverlapConflictStrategy",
    "FormatVariationStrategy",
    "ContextDependencyStrategy",
    "CoverageGapStrategy",
    "EntityConfusionStrategy",
    "WeaknessType",
    "WeaknessReport",
]
