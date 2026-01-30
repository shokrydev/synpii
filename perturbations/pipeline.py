"""Composable perturbation pipeline."""

import random
from typing import List, Dict, Any, Optional, Type

from synpii.perturbations.base import BasePerturbation
from synpii.perturbations.ocr import OCRPerturbation, UmlautNormalization
from synpii.perturbations.bpe import BPEPerturbation, MidWordHyphenation
from synpii.perturbations.corruption import (
    GrammarCorruption,
    UmlautCorruption,
    CaseCorruption,
    SpacingCorruption,
)
from synpii.core.types import GeneratedDocument, Annotation
from synpii.core.span_tracker import SpanTracker


# Registry of available perturbations
PERTURBATION_REGISTRY: Dict[str, Type[BasePerturbation]] = {
    "ocr": OCRPerturbation,
    "umlaut_norm": UmlautNormalization,
    "bpe": BPEPerturbation,
    "hyphenation": MidWordHyphenation,
    "grammar": GrammarCorruption,
    "umlaut": UmlautCorruption,
    "case": CaseCorruption,
    "spacing": SpacingCorruption,
}


class PerturbationPipeline:
    """Composable pipeline for applying perturbations to documents.

    The pipeline:
    1. Selects entities to perturb based on rate
    2. Applies selected perturbations to entity text only
    3. Updates spans to maintain alignment

    Example:
        pipeline = PerturbationPipeline(
            perturbations=["ocr", "bpe"],
            rate=0.3,
        )
        perturbed_doc = pipeline.apply(doc)
    """

    def __init__(
        self,
        perturbations: List[str] = None,
        rate: float = 0.3,
        seed: int = None,
    ):
        """Initialize perturbation pipeline.

        Args:
            perturbations: List of perturbation names to include.
            rate: Overall rate of perturbation application.
            seed: Random seed for reproducibility.
        """
        self.rate = rate

        if seed is not None:
            random.seed(seed)

        # Initialize perturbation instances
        self.perturbations: List[BasePerturbation] = []
        perturbation_names = perturbations or ["ocr", "bpe"]

        for name in perturbation_names:
            if name in PERTURBATION_REGISTRY:
                self.perturbations.append(PERTURBATION_REGISTRY[name]())
            else:
                raise ValueError(
                    f"Unknown perturbation: {name}. "
                    f"Available: {list(PERTURBATION_REGISTRY.keys())}"
                )

    def apply(
        self,
        doc: GeneratedDocument,
        target_entity_types: List[str] = None,
    ) -> GeneratedDocument:
        """Apply perturbations to a document.

        Args:
            doc: Document to perturb.
            target_entity_types: Only perturb these entity types (all if None).

        Returns:
            New GeneratedDocument with perturbations applied.
        """
        if not self.perturbations or self.rate <= 0:
            return doc

        if not doc.annotations:
            return doc

        # Create span tracker from annotations
        tracker = SpanTracker()
        for ann in doc.annotations:
            from synpii.core.types import SpanInfo
            tracker.add_span(SpanInfo(
                text=ann.text,
                start=ann.start,
                end=ann.end,
                entity_type=ann.entity_type,
            ))

        text = doc.text
        perturbations_applied = []

        # Process each annotation
        for i, ann in enumerate(doc.annotations):
            # Check if we should perturb this entity
            if target_entity_types and ann.entity_type not in target_entity_types:
                continue

            if random.random() > self.rate:
                continue

            # Select and apply a perturbation
            perturbation = random.choice(self.perturbations)

            if perturbation.can_apply(ann.text):
                try:
                    text, new_span = tracker.apply_perturbation(
                        text=text,
                        span_index=i,
                        perturbation=perturbation,
                    )
                    perturbations_applied.append({
                        "entity_index": i,
                        "perturbation": perturbation.name,
                        "original": ann.text,
                        "perturbed": new_span.text,
                    })
                except Exception as e:
                    # Skip this perturbation on error
                    continue

        # Build new annotations from tracker
        new_annotations = tracker.to_annotations(source="perturbed")

        # Create new document
        return GeneratedDocument(
            id=doc.id,
            template_type=doc.template_type,
            text=text,
            annotations=new_annotations,
            metadata={
                **doc.metadata,
                "perturbations_applied": perturbations_applied,
                "perturbation_rate": self.rate,
            },
        )

    def apply_to_entity(self, entity_text: str) -> str:
        """Apply perturbations to a single entity string.

        Args:
            entity_text: Entity text to perturb.

        Returns:
            Perturbed text.
        """
        if random.random() > self.rate:
            return entity_text

        perturbation = random.choice(self.perturbations)
        if perturbation.can_apply(entity_text):
            return perturbation.apply(entity_text)
        return entity_text


class AdversarialPipeline(PerturbationPipeline):
    """Pre-configured adversarial perturbation pipeline.

    Includes all perturbations optimized for detection evasion testing.
    """

    def __init__(self, rate: float = 0.4, seed: int = None):
        """Initialize adversarial pipeline.

        Args:
            rate: Overall perturbation rate.
            seed: Random seed.
        """
        super().__init__(
            perturbations=["ocr", "bpe", "grammar", "umlaut", "case"],
            rate=rate,
            seed=seed,
        )


class OCRSimulationPipeline(PerturbationPipeline):
    """Pre-configured pipeline simulating OCR errors."""

    def __init__(self, rate: float = 0.5, seed: int = None):
        """Initialize OCR simulation pipeline."""
        super().__init__(
            perturbations=["ocr", "umlaut_norm", "spacing"],
            rate=rate,
            seed=seed,
        )
