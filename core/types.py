"""Core data types for SynPII."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class EntityType(str, Enum):
    """Supported entity types."""

    # Person-related
    PERSON = "PERSON"
    AGE = "AGE"

    # Date/Time
    DATE_TIME = "DATE_TIME"

    # Location
    LOCATION = "LOCATION"

    # Contact
    PHONE_NUMBER = "PHONE_NUMBER"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"

    # German healthcare IDs
    DE_KVNR = "DE_KVNR"
    DE_LANR = "DE_LANR"
    DE_BSNR = "DE_BSNR"
    DE_TELEMATIK_ID = "DE_TELEMATIK_ID"
    DE_POSTAL_CODE = "DE_POSTAL_CODE"

    # German personal IDs
    DE_PERSONAL_ID = "DE_PERSONAL_ID"
    DE_TAX_ID = "DE_TAX_ID"
    DE_SOCIAL_SECURITY = "DE_SOCIAL_SECURITY"
    DE_PASSPORT = "DE_PASSPORT"
    DE_DRIVER_LICENSE = "DE_DRIVER_LICENSE"

    # German business IDs
    DE_COMMERCIAL_REGISTER = "DE_COMMERCIAL_REGISTER"
    DE_VAT_CODE = "DE_VAT_CODE"
    DE_LICENSE_PLATE = "DE_LICENSE_PLATE"

    # Financial
    IBAN = "IBAN"

    # Organization
    ORGANIZATION = "ORGANIZATION"


@dataclass
class Entity:
    """A generated PII entity with metadata.

    Attributes:
        entity_type: The type of entity (e.g., PERSON, DE_KVNR).
        value: The primary generated value.
        variants: Alternative representations of the same entity.
        metadata: Additional metadata (gender, region, etc.).
    """

    entity_type: str
    value: str
    variants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.variants:
            self.variants = [self.value]

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "variants": self.variants,
            "metadata": self.metadata,
        }


@dataclass
class SpanInfo:
    """Tracks entity position in text.

    Attributes:
        text: The actual text at this span.
        start: Start character offset.
        end: End character offset.
        entity_type: Type of entity at this span.
        metadata: Additional span metadata.
    """

    text: str
    start: int
    end: int
    entity_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate span
        if self.end < self.start:
            raise ValueError(f"Invalid span: end ({self.end}) < start ({self.start})")
        if self.end - self.start != len(self.text):
            raise ValueError(
                f"Span length mismatch: {self.end - self.start} != {len(self.text)}"
            )

    def overlaps(self, other: "SpanInfo") -> bool:
        """Check if this span overlaps with another."""
        return not (self.end <= other.start or other.end <= self.start)

    def contains(self, other: "SpanInfo") -> bool:
        """Check if this span fully contains another."""
        return self.start <= other.start and self.end >= other.end


@dataclass
class Annotation:
    """Ground truth PII annotation for benchmarking.

    Attributes:
        entity_type: Type of entity.
        text: The annotated text.
        start: Start character offset.
        end: End character offset.
        source: Origin of annotation (template, perturbation, etc.).
    """

    entity_type: str
    text: str
    start: int
    end: int
    source: str = "template"

    def to_dict(self) -> dict:
        return asdict(self)

    def __post_init__(self):
        # Validate annotation
        if self.end < self.start:
            raise ValueError(f"Invalid annotation: end ({self.end}) < start ({self.start})")


@dataclass
class GeneratedDocument:
    """A generated document with annotations.

    Attributes:
        id: Unique document identifier.
        template_type: Template used for generation.
        text: The generated text content.
        annotations: List of PII annotations.
        metadata: Additional document metadata.
    """

    id: str
    template_type: str
    text: str
    annotations: List[Annotation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "template_type": self.template_type,
            "text": self.text,
            "annotations": [a.to_dict() for a in self.annotations],
            "metadata": self.metadata,
        }

    def verify_annotations(self) -> bool:
        """Verify all annotations match their text spans."""
        for ann in self.annotations:
            if self.text[ann.start : ann.end] != ann.text:
                return False
        return True

    def get_entities_by_type(self, entity_type: str) -> List[Annotation]:
        """Get all annotations of a specific type."""
        return [a for a in self.annotations if a.entity_type == entity_type]

    def has_overlapping_entities(self) -> bool:
        """Check if any annotations overlap."""
        sorted_anns = sorted(self.annotations, key=lambda a: a.start)
        for i in range(len(sorted_anns) - 1):
            if sorted_anns[i].end > sorted_anns[i + 1].start:
                return True
        return False
