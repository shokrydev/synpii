"""Adversarial scenario recipes for robustness evaluation.

Each recipe implements the generative logic for a specific failure mode,
using adversarial patterns defined in the lexicon.
"""

from abc import ABC, abstractmethod
import random
from typing import List, Optional, Dict, Any

from synpii.adversarial.types import AdversarialType, AdversarialScenario, AdversarialSample
from synpii.generators.base import GeneratorRegistry
from synpii.core.lexicon import GermanLexicon
from synpii.templates.engine import TemplateEngine


class AdversarialRecipe(ABC):
    """Abstract base class for adversarial generation recipes."""

    adversarial_type: AdversarialType = None

    def __init__(
        self,
        generators: GeneratorRegistry = None,
        lexicon: GermanLexicon = None,
        template_engine: TemplateEngine = None,
    ):
        """Initialize recipe.

        Args:
            generators: Entity generator registry.
            lexicon: German lexicon for values.
            template_engine: Template engine for rendering.
        """
        self.generators = generators
        self.lexicon = lexicon
        self._engine = template_engine or TemplateEngine(lexicon=lexicon)

    @abstractmethod
    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate samples for a specific adversarial scenario.

        Args:
            scenario: The scenario description to target.
            count: Number of samples to generate.

        Returns:
            List of AdversarialSample objects.
        """
        pass


class OverlapScenario(AdversarialRecipe):
    """Recipe for generating overlapping entity scenarios."""

    adversarial_type = AdversarialType.OVERLAP_CONFLICT

    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate overlap conflict samples."""
        samples = []
        entity_type = scenario.entity_type
        
        # Get patterns from lexicon
        all_patterns = self.lexicon.get_patterns("overlap_patterns") if self.lexicon else {}
        
        # Find relevant patterns for this entity type
        patterns = []
        for key, p_list in all_patterns.items():
            if entity_type in key.upper():
                patterns.extend(p_list)

        if not patterns:
            # Fallback to default postal/location if nothing found
            patterns = all_patterns.get("postal_location", ["{{DE_POSTAL_CODE}} {{LOCATION}}"])

        for _ in range(count):
            pattern = random.choice(patterns)
            text, annotations = self._engine.render_string(pattern, generators=self.generators)
            
            entities = [
                {"type": a.entity_type, "text": a.text, "start": a.start, "end": a.end}
                for a in annotations
            ]

            samples.append(AdversarialSample(
                text=text,
                expected_entities=entities,
                adversarial_type=self.adversarial_type,
                difficulty=3,
                metadata={"pattern": pattern},
            ))

        return samples


class FormatScenario(AdversarialRecipe):
    """Recipe for generating format variation scenarios."""

    adversarial_type = AdversarialType.FORMAT_VARIATION

    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate format variation samples."""
        samples = []
        entity_type = scenario.entity_type
        
        all_variations = self.lexicon.get_patterns("format_variations") if self.lexicon else {}
        variations = all_variations.get(entity_type, {})

        if not variations:
            return samples

        for _ in range(count):
            var_name = random.choice(list(variations.keys()))
            pattern = variations[var_name]
            
            # Prepare context for rendering
            context = self._prepare_format_context(entity_type)
            text, annotations = self._engine.render_string(
                pattern, generators=self.generators, context=context
            )

            # Ensure the whole output is annotated as the target entity if no sub-annotations found
            entities = [
                {"type": a.entity_type, "text": a.text, "start": a.start, "end": a.end}
                for a in annotations
            ] or [
                {"type": entity_type, "text": text, "start": 0, "end": len(text)}
            ]

            samples.append(AdversarialSample(
                text=text,
                expected_entities=entities,
                adversarial_type=self.adversarial_type,
                difficulty=2 if var_name == "standard" else 4,
                metadata={"variation": var_name},
            ))

        return samples

    def _prepare_format_context(self, entity_type: str) -> Dict[str, Any]:
        """Prepare specific context values for format placeholders."""
        if entity_type == "DATE_TIME":
            d, m, y = random.randint(1, 28), random.randint(1, 12), random.randint(1950, 2024)
            months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                      "Juli", "August", "September", "Oktober", "November", "Dezember"]
            return {
                "day": (d, None),
                "month": (m, None),
                "year": (y, None),
                "month_name": (months[m-1], None)
            }
        
        if entity_type == "PHONE_NUMBER":
            area = random.choice(["030", "040", "069", "089", "0221"])
            num = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            return {
                "area": (area, None),
                "area_short": (area[1:], None),
                "num": (num, None),
                "n1": (num[:3], None),
                "n2": (num[3:], None),
            }
            
        if entity_type == "DE_KVNR":
            letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            return {
                "letter": (letter, None),
                "digits": (digits, None),
                "kvnr": (letter + digits, "DE_KVNR")
            }
            
        return {}


class ContextScenario(AdversarialRecipe):
    """Recipe for generating context-dependency scenarios."""

    adversarial_type = AdversarialType.CONTEXT_DEPENDENCY

    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate context dependency samples."""
        samples = []
        entity_type = scenario.entity_type
        
        all_patterns = self.lexicon.get_patterns("context_patterns") if self.lexicon else {}
        patterns = all_patterns.get(entity_type, {})

        if not patterns:
            # Default fallback patterns
            patterns = {
                "no_context": "{{value}}",
                "generic": "Der Wert ist {{value}}"
            }

        for _ in range(count):
            context_type = random.choice(list(patterns.keys()))
            pattern = patterns[context_type]

            # Generate entity value via registry
            if self.generators and self.generators.is_available(entity_type):
                entity = self.generators.generate(entity_type)
                value = entity.value
            else:
                value = f"[{entity_type}]"

            # Render with explicit value
            text, annotations = self._engine.render_string(
                pattern, generators=self.generators, context={"value": (value, entity_type)}
            )

            entities = [
                {"type": a.entity_type, "text": a.text, "start": a.start, "end": a.end}
                for a in annotations
            ]

            samples.append(AdversarialSample(
                text=text,
                expected_entities=entities,
                adversarial_type=self.adversarial_type,
                difficulty=2 if context_type != "no_context" else 5,
                metadata={"context_type": context_type},
            ))

        return samples


class CoverageScenario(AdversarialRecipe):
    """Recipe for generating coverage gap scenarios."""

    adversarial_type = AdversarialType.COVERAGE_GAP

    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate coverage gap samples."""
        samples = []
        entity_type = scenario.entity_type

        for _ in range(count):
            # Generate entity value
            if self.generators and self.generators.is_available(entity_type):
                entity = self.generators.generate(entity_type)
                value = entity.value
            else:
                value = f"[{entity_type}]"

            # Use TemplateEngine for consistent rendering
            pattern = "Der Wert {{value}} sollte erkannt werden."
            text, annotations = self._engine.render_string(
                pattern, generators=self.generators, context={"value": (value, entity_type)}
            )

            entities = [
                {"type": a.entity_type, "text": a.text, "start": a.start, "end": a.end}
                for a in annotations
            ]

            samples.append(AdversarialSample(
                text=text,
                expected_entities=entities,
                adversarial_type=self.adversarial_type,
                difficulty=5,
                metadata={"note": "No recognizer available"},
            ))

        return samples


class ConfusionScenario(AdversarialRecipe):
    """Recipe for generating entity type confusion scenarios."""

    adversarial_type = AdversarialType.ENTITY_CONFUSION

    def generate(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate entity confusion samples."""
        samples = []
        entity_type = scenario.entity_type
        
        all_patterns = self.lexicon.get_patterns("confusion_patterns") if self.lexicon else {}
        
        # Determine the key for confusion patterns
        confusion_key = f"{entity_type}_ORGANIZATION" # Default common confusion
        patterns = all_patterns.get(confusion_key, [])

        for _ in range(count):
            if patterns:
                pattern = random.choice(patterns)
                
                # Check if we need a last name for the pattern
                last_name = self.lexicon.sample_last_name() if self.lexicon else "Müller"
                text, annotations = self._engine.render_string(
                    pattern, generators=self.generators, context={"last_name": (last_name, None)}
                )
                
                # Heuristic: Dr. is usually PERSON
                expected_type = "PERSON" if "Dr." in text else "ORGANIZATION"
            else:
                # Fallback to isolation
                if self.generators and self.generators.is_available(entity_type):
                    entity = self.generators.generate(entity_type)
                    text, expected_type = entity.value, entity_type
                    annotations = []
                else:
                    text, expected_type = f"[{entity_type}]", entity_type
                    annotations = []

            entities = [
                {"type": a.entity_type, "text": a.text, "start": a.start, "end": a.end}
                for a in annotations
            ] or [
                {"type": expected_type, "text": text, "start": 0, "end": len(text)}
            ]

            samples.append(AdversarialSample(
                text=text,
                expected_entities=entities,
                adversarial_type=self.adversarial_type,
                difficulty=4,
                metadata={"confusion_pair": (entity_type, "ORGANIZATION")},
            ))

        return samples
