"""Core types for adversarial scenario generation and robustness testing.

Uses state-of-the-art research terminology (Adversarial NLP, Robustness Evaluation).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class AdversarialType(str, Enum):
    """Types of adversarial scenarios designed to test model robustness."""

    # Overlap between entity types (e.g. PLZ in LOCATION)
    OVERLAP_CONFLICT = "OVERLAP_CONFLICT"
    # Format variation (e.g. non-standard separators)
    FORMAT_VARIATION = "FORMAT_VARIATION"
    # Context dependency (e.g. missing trigger words)
    CONTEXT_DEPENDENCY = "CONTEXT_DEPENDENCY"
    # Recognizer coverage gaps
    COVERAGE_GAP = "COVERAGE_GAP"
    # Type confusion (e.g. PERSON vs ORGANIZATION)
    ENTITY_CONFUSION = "ENTITY_CONFUSION"
    # Data leakage through synthetic artifacts
    LEAKAGE = "LEAKAGE"


@dataclass
class AdversarialScenario:
    """A research scenario targeting specific robustness failure modes.

    Attributes:
        adversarial_type: The type of scenario to generate.
        entity_type: Primary affected entity type.
        description: Description of the research hypothesis.
        confidence: Estimated probability of model failure (0.0-1.0).
        evidence: Data supporting the scenario (e.g. error logs).
    """

    adversarial_type: AdversarialType
    entity_type: str
    description: str
    confidence: float = 0.5
    evidence: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "adversarial_type": self.adversarial_type.value,
            "entity_type": self.entity_type,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class AdversarialSample:
    """A synthetic sample designed to identify failure boundaries.

    Attributes:
        text: The generated text content.
        expected_entities: Ground truth annotations.
        adversarial_type: The failure mode being challenged.
        difficulty: Relative difficulty based on scenario complexity (1-5).
        metadata: Additional generation metadata.
    """

    text: str
    expected_entities: List[Dict[str, Any]]  # {type, start, end, text}
    adversarial_type: AdversarialType
    difficulty: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdversarialTestResult:
    """Evaluation result of a model on an adversarial sample.

    Matches standard robustness evaluation metrics.
    """

    sample: AdversarialSample
    detected_entities: List[Dict[str, Any]]
    true_positives: int
    false_positives: int
    false_negatives: int
    passed: bool = False

    @property
    def precision(self) -> float:
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
