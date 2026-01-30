"""Span tracking through text transformations.

Maintains accurate entity positions through perturbations by:
1. Applying perturbations to entity text only
2. Recomputing span via direct string search
3. Tracking transformation history for debugging
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from copy import deepcopy

from synpii.core.types import SpanInfo, Annotation, GeneratedDocument


@dataclass
class TransformationRecord:
    """Record of a single transformation applied to text."""

    transform_type: str  # "perturbation", "replacement", etc.
    original_text: str
    new_text: str
    original_span: Tuple[int, int]
    new_span: Tuple[int, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SpanTracker:
    """Track entity spans through text transformations.

    Key insight: Apply perturbations to entity text ONLY, then recompute
    spans via direct string search. This guarantees alignment.

    Example:
        tracker = SpanTracker()

        # Add initial spans
        tracker.add_span(SpanInfo("Goethestraße", 10, 22, "LOCATION"))

        # Apply perturbation to a span
        text, new_span = tracker.apply_perturbation(
            text="Patient wohnt in Goethestraße 5",
            span_index=0,
            perturbation=ocr_perturbation,
        )
        # Result: "Patient wohnt in Goethestrasse 5" with updated span
    """

    def __init__(self):
        """Initialize span tracker."""
        self.spans: List[SpanInfo] = []
        self.history: List[TransformationRecord] = []

    def add_span(self, span: SpanInfo) -> int:
        """Add a span to track.

        Args:
            span: SpanInfo to track.

        Returns:
            Index of the added span.
        """
        self.spans.append(span)
        return len(self.spans) - 1

    def add_spans(self, spans: List[SpanInfo]) -> None:
        """Add multiple spans to track.

        Args:
            spans: List of SpanInfo objects.
        """
        self.spans.extend(spans)

    def get_span(self, index: int) -> Optional[SpanInfo]:
        """Get a span by index.

        Args:
            index: Span index.

        Returns:
            SpanInfo or None if index out of range.
        """
        if 0 <= index < len(self.spans):
            return self.spans[index]
        return None

    def apply_perturbation(
        self,
        text: str,
        span_index: int,
        perturbation: "BasePerturbation",
    ) -> Tuple[str, SpanInfo]:
        """Apply perturbation to a specific span.

        The key approach:
        1. Extract entity text from span
        2. Apply perturbation to entity only
        3. Replace in full text
        4. Compute new span via string length

        Args:
            text: Full text containing the entity.
            span_index: Index of span to perturb.
            perturbation: Perturbation to apply.

        Returns:
            Tuple of (new_text, new_span).
        """
        span = self.spans[span_index]

        # Extract entity text
        entity_text = text[span.start:span.end]

        # Verify alignment
        if entity_text != span.text:
            raise ValueError(
                f"Span text mismatch: expected '{span.text}' but found '{entity_text}'"
            )

        # Apply perturbation to entity only
        perturbed_entity = perturbation.apply(entity_text)

        # Reconstruct text with perturbed entity
        new_text = text[:span.start] + perturbed_entity + text[span.end:]

        # Compute new span (simple: same start, new length)
        new_span = SpanInfo(
            text=perturbed_entity,
            start=span.start,
            end=span.start + len(perturbed_entity),
            entity_type=span.entity_type,
            metadata={**span.metadata, "perturbed": True},
        )

        # Update tracked span
        self.spans[span_index] = new_span

        # Record transformation
        self.history.append(TransformationRecord(
            transform_type="perturbation",
            original_text=entity_text,
            new_text=perturbed_entity,
            original_span=(span.start, span.end),
            new_span=(new_span.start, new_span.end),
            metadata={"perturbation_type": perturbation.__class__.__name__},
        ))

        # Adjust positions of subsequent spans
        length_diff = len(perturbed_entity) - len(entity_text)
        if length_diff != 0:
            self._adjust_spans_after(span_index, length_diff)

        return new_text, new_span

    def _adjust_spans_after(self, affected_index: int, length_diff: int) -> None:
        """Adjust span positions after a transformation.

        Args:
            affected_index: Index of the transformed span.
            length_diff: Change in text length (positive = longer).
        """
        affected_span = self.spans[affected_index]

        for i, span in enumerate(self.spans):
            if i == affected_index:
                continue

            # Only adjust spans that come after the affected one
            if span.start >= affected_span.end - length_diff:
                self.spans[i] = SpanInfo(
                    text=span.text,
                    start=span.start + length_diff,
                    end=span.end + length_diff,
                    entity_type=span.entity_type,
                    metadata=span.metadata,
                )

    def verify_all_spans(self, text: str) -> bool:
        """Verify all tracked spans match the text.

        Args:
            text: Text to verify against.

        Returns:
            True if all spans match, False otherwise.
        """
        for span in self.spans:
            if text[span.start:span.end] != span.text:
                return False
        return True

    def to_annotations(self, source: str = "generated") -> List[Annotation]:
        """Convert tracked spans to annotations.

        Args:
            source: Source label for annotations.

        Returns:
            List of Annotation objects.
        """
        return [
            Annotation(
                entity_type=span.entity_type,
                text=span.text,
                start=span.start,
                end=span.end,
                source=source,
            )
            for span in self.spans
        ]

    def from_document(self, doc: GeneratedDocument) -> "SpanTracker":
        """Load spans from a generated document.

        Args:
            doc: GeneratedDocument with annotations.

        Returns:
            Self for chaining.
        """
        self.spans = [
            SpanInfo(
                text=ann.text,
                start=ann.start,
                end=ann.end,
                entity_type=ann.entity_type,
            )
            for ann in doc.annotations
        ]
        return self


def track_template_replacement(
    template: str,
    replacements: List[Dict[str, Any]],
) -> Tuple[str, List[SpanInfo]]:
    """Track entity positions through template replacement.

    This function handles the common case of filling a template with
    entity values while maintaining accurate span positions.

    Strategy:
    1. Sort replacements by position (reverse order)
    2. Replace from end to start (preserves earlier positions)
    3. Compute final positions based on replacement order

    Args:
        template: Template string with placeholders.
        replacements: List of dicts with keys:
            - start: Placeholder start position
            - end: Placeholder end position
            - value: Replacement value
            - entity_type: Entity type (or None for non-PII)

    Returns:
        Tuple of (filled_text, spans).
    """
    # Sort by position, descending (replace from end first)
    sorted_replacements = sorted(replacements, key=lambda r: r["start"], reverse=True)

    text = template
    position_adjustments: List[Tuple[int, int]] = []  # (position, adjustment)

    # First pass: do replacements and track adjustments
    for repl in sorted_replacements:
        old_len = repl["end"] - repl["start"]
        new_len = len(repl["value"])
        adjustment = new_len - old_len

        text = text[:repl["start"]] + repl["value"] + text[repl["end"]:]
        position_adjustments.append((repl["start"], adjustment))

    # Second pass: compute final positions
    # Need to re-sort by original position (ascending) for span creation
    sorted_for_spans = sorted(replacements, key=lambda r: r["start"])

    spans = []
    for repl in sorted_for_spans:
        if repl.get("entity_type") is None:
            continue  # Skip non-PII

        # Calculate final position by applying all adjustments
        # from earlier replacements
        final_start = repl["start"]
        for adj_pos, adj_val in position_adjustments:
            if adj_pos < repl["start"]:
                final_start += adj_val

        spans.append(SpanInfo(
            text=repl["value"],
            start=final_start,
            end=final_start + len(repl["value"]),
            entity_type=repl["entity_type"],
        ))

    return text, spans


def find_entity_positions(
    text: str,
    entity_value: str,
    entity_type: str,
    start_from: int = 0,
) -> List[SpanInfo]:
    """Find all occurrences of an entity value in text.

    Useful for post-hoc annotation when spans weren't tracked
    during generation.

    Args:
        text: Text to search.
        entity_value: Entity value to find.
        entity_type: Type to assign to found spans.
        start_from: Start searching from this position.

    Returns:
        List of SpanInfo for all occurrences.
    """
    spans = []
    pos = start_from

    while True:
        pos = text.find(entity_value, pos)
        if pos == -1:
            break

        spans.append(SpanInfo(
            text=entity_value,
            start=pos,
            end=pos + len(entity_value),
            entity_type=entity_type,
        ))

        pos += 1  # Move past this occurrence

    return spans
