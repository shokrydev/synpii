"""Adversarial research module for SynPII.

Provides generative recipes and orchestrators for creating targeted
adversarial scenarios that test the robustness of PII detection models.
"""

from synpii.adversarial.types import (
    AdversarialType,
    AdversarialScenario,
    AdversarialSample,
    AdversarialTestResult,
)
from synpii.adversarial.generator import AdversarialGenerator
from synpii.adversarial.scenarios import (
    AdversarialRecipe,
    OverlapScenario,
    FormatScenario,
    ContextScenario,
    CoverageScenario,
    ConfusionScenario,
)

__all__ = [
    "AdversarialType",
    "AdversarialScenario",
    "AdversarialSample",
    "AdversarialTestResult",
    "AdversarialGenerator",
    "AdversarialRecipe",
    "OverlapScenario",
    "FormatScenario",
    "ContextScenario",
    "CoverageScenario",
    "ConfusionScenario",
]
