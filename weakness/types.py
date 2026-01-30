"""Types for weakness analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class WeaknessType(str, Enum):
    """Types of detection weaknesses."""

    # Overlap between entity types
    OVERLAP_CONFLICT = "OVERLAP_CONFLICT"
    # Entity format differs from expected pattern
    FORMAT_VARIATION = "FORMAT_VARIATION"
    # Detection needs specific context words
    CONTEXT_DEPENDENCY = "CONTEXT_DEPENDENCY"
    # No recognizer detects this entity type
    COVERAGE_GAP = "COVERAGE_GAP"
    # Wrong entity type assigned
    ENTITY_CONFUSION = "ENTITY_CONFUSION"
    # PII survives anonymization
    LEAKAGE = "LEAKAGE"


@dataclass
class WeaknessReport:
    """Report of a detected weakness.

    Attributes:
        weakness_type: Type of weakness.
        entity_type: Primary affected entity type.
        description: Human-readable description.
        confidence: Confidence score (0.0-1.0).
        evidence: Supporting evidence data.
        suggested_fix: Optional suggestion for improvement.
    """

    weakness_type: WeaknessType
    entity_type: str
    description: str
    confidence: float = 0.5
    evidence: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "weakness_type": self.weakness_type.value,
            "entity_type": self.entity_type,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class WeaknessTestCase:
    """A test case designed to expose a specific weakness.

    Attributes:
        text: The test text.
        expected_entities: List of entities that should be detected.
        weakness_type: Type of weakness being tested.
        difficulty: Relative difficulty (1-5).
        metadata: Additional test case metadata.
    """

    text: str
    expected_entities: List[Dict[str, Any]]  # {type, start, end, text}
    weakness_type: WeaknessType
    difficulty: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeaknessTestResult:
    """Result of running a weakness test case.

    Attributes:
        test_case: The test case that was run.
        detected_entities: Entities actually detected.
        true_positives: Correctly detected entities.
        false_positives: Incorrectly detected entities.
        false_negatives: Missed entities.
        passed: Whether the test passed.
    """

    test_case: WeaknessTestCase
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
