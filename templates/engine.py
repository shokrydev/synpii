"""Template engine for generating documents with tracked PII.

Uses {{entity_type}} or {{entity_type:name}} placeholders that are
filled with generated values while tracking span positions.
"""

import re
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from synpii.core.types import Entity, Annotation, GeneratedDocument
from synpii.core.lexicon import GermanLexicon
from synpii.core.span_tracker import track_template_replacement
from synpii.generators.base import GeneratorRegistry
from synpii.generators.clinical.content import ClinicalContentGenerator


class TemplateEngine:
    """Template processor for generating documents with PII tracking.

    Templates use {{placeholder}} syntax:
    - {{PERSON}} - Generate and insert a PERSON entity
    - {{PERSON:patient}} - Named placeholder (reusable)
    - {{DATE_TIME:birth}} - Named date
    - {{non_pii:diagnosis}} - Non-PII content (not annotated)

    Example template:
        Patient: {{PERSON:patient}}, geb. {{DATE_TIME:birth}}
        Versichertennummer: {{DE_KVNR}}

        Der {{non_pii:age_ref}} {{PERSON:patient_ref}} ...
    """

    # Regex to match {{placeholder}} or {{type:name}}
    PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)(?::(\w+))?\}\}')

    # Non-PII placeholder types (content, not entities)
    NON_PII_TYPES = {
        'non_pii', 'department', 'specialty', 'ward', 'diagnosis',
        'symptom', 'duration', 'finding', 'assessment', 'therapy',
        'occupation', 'medication', 'vital_signs', 'followup_weeks',
        'diagnosis_year', 'bp_systolic', 'bp_diastolic', 'pulse',
    }

    def __init__(
        self,
        templates_dir: Path = None,
        lexicon: GermanLexicon = None,
    ):
        """Initialize template engine.

        Args:
            templates_dir: Directory containing template files.
            lexicon: GermanLexicon for value lookup.
        """
        self.lexicon = lexicon
        self.templates: Dict[str, str] = {}
        self.clinical_content = ClinicalContentGenerator(lexicon)

        # Load templates from directory
        if templates_dir:
            templates_dir = Path(templates_dir)
            if templates_dir.exists():
                for template_file in templates_dir.glob("*.txt"):
                    self.templates[template_file.stem] = template_file.read_text(encoding="utf-8")

    def add_template(self, name: str, content: str) -> None:
        """Add a template programmatically.

        Args:
            name: Template name.
            content: Template content with {{placeholders}}.
        """
        self.templates[name] = content

    def generate(
        self,
        template_type: str = None,
        generators: GeneratorRegistry = None,
        doc_id: str = None,
        context: Dict[str, Any] = None,
    ) -> GeneratedDocument:
        """Generate a document from a template.

        Args:
            template_type: Template name (random if not specified).
            generators: Generator registry for creating entities.
            doc_id: Document ID (auto-generated if not specified).
            context: Pre-defined values for named placeholders.

        Returns:
            GeneratedDocument with text and annotations.
        """
        # Select template
        if template_type is None:
            if not self.templates:
                raise ValueError("No templates loaded")
            template_type = random.choice(list(self.templates.keys()))

        if template_type not in self.templates:
            raise ValueError(
                f"Unknown template: {template_type}. "
                f"Available: {list(self.templates.keys())}"
            )

        template = self.templates[template_type]

        if doc_id is None:
            doc_id = f"doc_{random.randint(10000, 99999)}"

        # Generate context if not provided
        if context is None:
            context = self._generate_context(template, generators)

        # Fill template and track spans
        text, annotations = self._fill_template(template, context)

        return GeneratedDocument(
            id=doc_id,
            template_type=template_type,
            text=text,
            annotations=annotations,
            metadata={"context_keys": list(context.keys())},
        )

    def _generate_context(
        self,
        template: str,
        generators: GeneratorRegistry,
    ) -> Dict[str, Tuple[str, Optional[str]]]:
        """Generate values for all placeholders in template.

        Returns dict mapping placeholder names to (value, entity_type) tuples.
        entity_type is None for non-PII content.
        """
        context: Dict[str, Tuple[str, Optional[str]]] = {}

        # Find all placeholders
        for match in self.PLACEHOLDER_PATTERN.finditer(template):
            placeholder_type = match.group(1)
            placeholder_name = match.group(2) or placeholder_type

            # Skip if already generated (named placeholders reuse)
            if placeholder_name in context:
                continue

            # Generate value based on type
            value, entity_type = self._generate_placeholder_value(
                placeholder_type, placeholder_name, generators, context
            )
            context[placeholder_name] = (value, entity_type)

        return context

    def _generate_placeholder_value(
        self,
        placeholder_type: str,
        placeholder_name: str,
        generators: GeneratorRegistry,
        context: Dict[str, Tuple[str, Optional[str]]],
    ) -> Tuple[str, Optional[str]]:
        """Generate a value for a specific placeholder.

        Returns (value, entity_type) tuple.
        """
        # Handle non-PII types
        if placeholder_type.lower() in self.NON_PII_TYPES or placeholder_type == 'non_pii':
            return self._generate_non_pii(placeholder_name), None

        # Handle reference to existing entity (e.g., patient_ref)
        if placeholder_name.endswith('_ref'):
            base_name = placeholder_name[:-4]  # Remove '_ref'
            if base_name in context:
                # Create reference form (e.g., "Herr Müller")
                base_value, base_type = context[base_name]
                if base_type == "PERSON":
                    # Extract last name and add salutation
                    parts = base_value.split()
                    last_name = parts[-1] if parts else base_value
                    # Determine gender from first name if possible
                    salutation = random.choice(["Herr", "Frau"])
                    return f"{salutation} {last_name}", None  # Not PII itself
            return placeholder_name, None

        # Handle entity types
        if generators and generators.is_available(placeholder_type):
            entity = generators.generate(placeholder_type)
            return entity.value, placeholder_type

        # Handle special cases
        if placeholder_type == "PERSON" and generators:
            if "doctor" in placeholder_name.lower():
                entity = generators.generate("PERSON", with_title=True, title_type="medical")
            else:
                entity = generators.generate("PERSON")
            return entity.value, "PERSON"

        # Fallback to non-PII
        return self._generate_non_pii(placeholder_name), None

    def _generate_non_pii(self, name: str) -> str:
        """Generate non-PII content based on name hint."""
        name_lower = name.lower()

        if 'diagnosis' in name_lower:
            return self.clinical_content.get_diagnosis()
        elif 'symptom' in name_lower:
            return self.clinical_content.get_symptom()
        elif 'medication' in name_lower:
            return self.clinical_content.get_medication()
        elif 'department' in name_lower:
            return self.clinical_content.get_department()
        elif 'specialty' in name_lower:
            return self.clinical_content.get_specialty()
        elif 'duration' in name_lower:
            return self.clinical_content.get_duration()
        elif 'finding' in name_lower:
            return self.clinical_content.get_finding()
        elif 'assessment' in name_lower:
            return self.clinical_content.get_assessment()
        elif 'therapy' in name_lower:
            return self.clinical_content.get_therapy()
        elif 'occupation' in name_lower:
            return self.clinical_content.get_occupation()
        elif 'ward' in name_lower:
            return self.clinical_content.get_ward()
        elif 'followup_weeks' in name_lower:
            return str(random.randint(2, 8))
        elif 'diagnosis_year' in name_lower:
            return str(random.randint(2015, 2023))
        elif 'bp_systolic' in name_lower:
            return str(random.randint(110, 160))
        elif 'bp_diastolic' in name_lower:
            return str(random.randint(60, 95))
        elif 'pulse' in name_lower:
            return str(random.randint(55, 100))
        else:
            return f"[{name}]"

    def _fill_template(
        self,
        template: str,
        context: Dict[str, Tuple[str, Optional[str]]],
    ) -> Tuple[str, List[Annotation]]:
        """Fill template with values and track spans.

        Returns (filled_text, annotations).
        """
        # Collect all replacements
        replacements = []

        for match in self.PLACEHOLDER_PATTERN.finditer(template):
            placeholder_type = match.group(1)
            placeholder_name = match.group(2) or placeholder_type

            if placeholder_name in context:
                value, entity_type = context[placeholder_name]
                replacements.append({
                    "start": match.start(),
                    "end": match.end(),
                    "value": value,
                    "entity_type": entity_type,
                    "placeholder": placeholder_name,
                })

        # Use span tracker to fill template
        text, spans = track_template_replacement(template, replacements)

        # Convert spans to annotations
        annotations = [
            Annotation(
                entity_type=span.entity_type,
                text=span.text,
                start=span.start,
                end=span.end,
                source="template",
            )
            for span in spans
        ]

        return text, annotations

    @property
    def available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
