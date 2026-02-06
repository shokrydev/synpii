"""SynPII: Synthetic PII Generation Library.

A grammar-aware synthetic PII generation library for benchmarking detection systems.

Key features:
- PCFG-based generation with Zipfian frequency distributions
- German grammar awareness (gender, case, article agreement)
- Adversarial perturbation pipelines (OCR, BPE, corruption)
- Guaranteed span alignment through deterministic perturbation tracking
- Adversarial scenario generation API for research automation
"""

from synpii.core.types import (
    Entity,
    Annotation,
    GeneratedDocument,
    SpanInfo,
    EntityType,
)
from synpii.core.grammar import PCFGEngine
from synpii.core.lexicon import ValueLoader, GermanLexicon
from synpii.core.span_tracker import SpanTracker

__version__ = "0.1.0"
__all__ = [
    "SynPII",
    "Entity",
    "Annotation",
    "GeneratedDocument",
    "SpanInfo",
    "EntityType",
    "PCFGEngine",
    "ValueLoader",
    "GermanLexicon",
    "SpanTracker",
]


class SynPII:
    """Main interface for synthetic PII generation.

    Example:
        synpii = SynPII(preset="clinical_de")
        doc = synpii.generate_document()
        print(doc.text)
        print(doc.annotations)
    """

    PRESETS = {
        "clinical_de": {
            "entity_types": [
                "PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS",
                "DE_KVNR", "DE_LANR", "DE_BSNR", "DE_POSTAL_CODE", "ORGANIZATION", "AGE",
            ],
            "perturbation_rate": 0.0,
            "templates": "clinical",
        },
        "benchmark_adversarial": {
            "entity_types": [
                "PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS",
                "DE_KVNR", "DE_LANR", "DE_BSNR", "DE_POSTAL_CODE", "ORGANIZATION", "AGE",
            ],
            "perturbation_rate": 0.3,
            "perturbations": ["ocr", "bpe", "grammar"],
            "templates": "clinical",
        },
        "minimal": {
            "entity_types": ["PERSON", "DATE_TIME", "LOCATION"],
            "perturbation_rate": 0.0,
            "templates": "clinical",
        },
        "full_german": {
            "entity_types": [
                "PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS",
                "DE_KVNR", "DE_LANR", "DE_BSNR", "DE_POSTAL_CODE", "DE_TELEMATIK_ID",
                "ORGANIZATION", "AGE", "IBAN",
            ],
            "perturbation_rate": 0.0,
            "templates": "clinical",
        },
    }

    def __init__(
        self,
        preset: str = "clinical_de",
        values_dir: str = None,
        templates_dir: str = None,
        seed: int = None,
    ):
        """Initialize SynPII generator.

        Args:
            preset: Configuration preset name.
            values_dir: Custom values directory path.
            templates_dir: Custom templates directory path.
            seed: Random seed for reproducibility.
        """
        from pathlib import Path
        import random

        if preset not in self.PRESETS:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(self.PRESETS.keys())}")

        self.preset = preset
        self.config = self.PRESETS[preset].copy()
        self.seed = seed

        if seed is not None:
            random.seed(seed)

        # Set up paths
        base_dir = Path(__file__).parent
        self.values_dir = Path(values_dir) if values_dir else base_dir / "values"
        self.templates_dir = Path(templates_dir) if templates_dir else base_dir / "templates"

        # Initialize components lazily
        self._lexicon = None
        self._template_engine = None
        self._generators = None
        self._adversarial_generator = None
        self._perturbation_pipeline = None

    @property
    def lexicon(self):
        """Lazy-load lexicon."""
        if self._lexicon is None:
            from synpii.core.lexicon import GermanLexicon
            self._lexicon = GermanLexicon(self.values_dir)
        return self._lexicon

    @property
    def template_engine(self):
        """Lazy-load template engine."""
        if self._template_engine is None:
            from synpii.templates.engine import TemplateEngine
            self._template_engine = TemplateEngine(
                templates_dir=self.templates_dir / self.config.get("templates", "clinical"),
                lexicon=self.lexicon,
            )
        return self._template_engine

    @property
    def generators(self):
        """Lazy-load generators registry."""
        if self._generators is None:
            from synpii.generators import GeneratorRegistry
            self._generators = GeneratorRegistry(
                lexicon=self.lexicon,
                entity_types=self.config.get("entity_types", []),
            )
        return self._generators

    @property
    def adversarial_generator(self):
        """Lazy-load adversarial scenario generator."""
        if self._adversarial_generator is None:
            from synpii.adversarial.generator import AdversarialGenerator
            self._adversarial_generator = AdversarialGenerator(
                generators=self.generators,
                lexicon=self.lexicon,
                template_engine=self.template_engine,
            )
        return self._adversarial_generator

    @property
    def perturbation_pipeline(self):
        """Lazy-load perturbation pipeline."""
        if self._perturbation_pipeline is None:
            from synpii.perturbations.pipeline import PerturbationPipeline
            self._perturbation_pipeline = PerturbationPipeline(
                perturbations=self.config.get("perturbations", []),
                rate=self.config.get("perturbation_rate", 0.0),
            )
        return self._perturbation_pipeline

    def generate_entity(self, entity_type: str):
        """Generate a single entity of the specified type.

        Args:
            entity_type: The type of entity to generate (e.g., "PERSON", "DE_KVNR").

        Returns:
            Entity object with value and metadata.
        """
        return self.generators.generate(entity_type)

    def generate_document(self, template_type: str = None, doc_id: str = None):
        """Generate a document with tracked PII annotations.

        Args:
            template_type: Specific template to use (random if not specified).
            doc_id: Document ID (auto-generated if not specified).

        Returns:
            GeneratedDocument with text and annotations.
        """
        import random

        if doc_id is None:
            doc_id = f"doc_{random.randint(10000, 99999)}"

        # Generate document from template
        doc = self.template_engine.generate(
            template_type=template_type,
            generators=self.generators,
            doc_id=doc_id,
        )

        # Apply perturbations if configured
        if self.config.get("perturbation_rate", 0) > 0:
            doc = self.perturbation_pipeline.apply(doc)

        return doc

    def generate_dataset(
        self,
        count: int = 100,
        adversarial_rate: float = None,
        output_path: str = None,
    ):
        """Generate a dataset of documents.

        Args:
            count: Number of documents to generate.
            adversarial_rate: Override perturbation rate for this dataset.
            output_path: Optional path to save the dataset.

        Returns:
            List of GeneratedDocument objects.
        """
        from synpii.output.dataset import DatasetBuilder

        builder = DatasetBuilder(self)
        return builder.build(
            count=count,
            adversarial_rate=adversarial_rate,
            output_path=output_path,
        )
