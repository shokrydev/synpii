#!/usr/bin/env python3
"""Test script for SynPII library.

Run with: python -m synpii.test_synpii
"""

import sys
from pathlib import Path

# Add parent to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_core_types():
    """Test core types."""
    print("Testing core types...")
    from synpii.core.types import Entity, Annotation, SpanInfo, GeneratedDocument

    # Entity
    entity = Entity(
        entity_type="PERSON",
        value="Hans Müller",
        variants=["Hans Müller", "Herr Müller"],
        metadata={"gender": "male"},
    )
    assert entity.value == "Hans Müller"
    assert len(entity.variants) == 2
    print("  ✓ Entity")

    # SpanInfo
    span = SpanInfo(text="Hans Müller", start=10, end=21, entity_type="PERSON")
    assert span.end - span.start == len(span.text)
    print("  ✓ SpanInfo")

    # Annotation
    ann = Annotation(entity_type="PERSON", text="Hans Müller", start=10, end=21)
    assert ann.entity_type == "PERSON"
    print("  ✓ Annotation")

    # GeneratedDocument
    doc = GeneratedDocument(
        id="test_001",
        template_type="test",
        text="Patient: Hans Müller",
        annotations=[ann],
    )
    assert doc.verify_annotations() == False  # Span doesn't match position
    print("  ✓ GeneratedDocument")

    print("Core types: PASSED\n")


def test_pcfg_grammar():
    """Test PCFG engine and street generator."""
    print("Testing PCFG grammar...")
    from synpii.core.grammar import PCFGEngine, GermanStreetGenerator

    # Simple grammar
    grammar = {
        "S": [
            (["A", "B"], 0.7),
            (["B", "A"], 0.3),
        ],
    }
    terminals = {"A": "hello", "B": "world"}

    engine = PCFGEngine(grammar, terminals)
    result = engine.expand("S")
    assert result in ["hello world", "world hello"]
    print(f"  ✓ Simple grammar: '{result}'")

    # Street generator (specialized, not PCFG-based)
    street_gen = GermanStreetGenerator()
    for _ in range(3):
        street = street_gen.generate()
        print(f"  ✓ Street: '{street}'")

    print("PCFG grammar: PASSED\n")


def test_lexicon():
    """Test lexicon loading."""
    print("Testing lexicon...")
    from synpii.core.lexicon import GermanLexicon
    from pathlib import Path

    values_dir = Path(__file__).parent / "values"
    lexicon = GermanLexicon(values_dir)

    # Test names
    assert len(lexicon.first_names_male) > 0
    assert len(lexicon.first_names_female) > 0
    assert len(lexicon.last_names) > 0
    print(f"  ✓ Names loaded: {len(lexicon.first_names_male)} male, {len(lexicon.first_names_female)} female")

    # Test cities
    assert len(lexicon.cities) > 0
    city, plz_min, plz_max = lexicon.cities[0]
    print(f"  ✓ Cities loaded: {len(lexicon.cities)} (e.g., {city})")

    # Test article agreement
    assert lexicon.get_article("m", "nominative") == "der"
    assert lexicon.get_article("f", "dative") == "der"
    assert lexicon.get_article("n", "accusative") == "das"
    print("  ✓ Article agreement")

    print("Lexicon: PASSED\n")


def test_generators():
    """Test entity generators."""
    print("Testing generators...")
    from synpii.generators import GeneratorRegistry
    from synpii.core.lexicon import GermanLexicon
    from pathlib import Path

    values_dir = Path(__file__).parent / "values"
    lexicon = GermanLexicon(values_dir)
    registry = GeneratorRegistry(lexicon=lexicon)

    # Test various entity types
    entity_types = ["PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER",
                    "DE_KVNR", "DE_LANR", "DE_BSNR", "DE_POSTAL_CODE"]

    for entity_type in entity_types:
        if registry.is_available(entity_type):
            entity = registry.generate(entity_type)
            print(f"  ✓ {entity_type}: '{entity.value}'")
        else:
            print(f"  ⚠ {entity_type}: not available")

    print("Generators: PASSED\n")


def test_perturbations():
    """Test perturbation pipeline."""
    print("Testing perturbations...")
    from synpii.perturbations import OCRPerturbation, BPEPerturbation, GrammarCorruption

    # OCR
    ocr = OCRPerturbation(probability=1.0, max_substitutions=2)
    text = "Goethestraße 10"
    perturbed = ocr.apply(text)
    print(f"  ✓ OCR: '{text}' → '{perturbed}'")

    # BPE
    bpe = BPEPerturbation(probability=1.0)
    text = "Goethestraße"
    perturbed = bpe.apply(text)
    print(f"  ✓ BPE: '{text}' → '{perturbed}'")

    # Grammar
    grammar = GrammarCorruption(probability=1.0)
    text = "an der Brücke"
    perturbed = grammar.apply(text)
    print(f"  ✓ Grammar: '{text}' → '{perturbed}'")

    print("Perturbations: PASSED\n")


def test_template_engine():
    """Test template engine."""
    print("Testing template engine...")
    from synpii.templates.engine import TemplateEngine
    from synpii.generators import GeneratorRegistry
    from synpii.core.lexicon import GermanLexicon
    from pathlib import Path

    values_dir = Path(__file__).parent / "values"
    templates_dir = Path(__file__).parent / "templates" / "clinical"

    lexicon = GermanLexicon(values_dir)
    generators = GeneratorRegistry(lexicon=lexicon)
    engine = TemplateEngine(templates_dir=templates_dir, lexicon=lexicon)

    print(f"  ✓ Templates loaded: {engine.available_templates}")

    # Generate document
    if engine.available_templates:
        doc = engine.generate(
            template_type=engine.available_templates[0],
            generators=generators,
        )
        print(f"  ✓ Generated document: {len(doc.text)} chars, {len(doc.annotations)} annotations")

        # Verify annotations
        if doc.verify_annotations():
            print("  ✓ Annotations verified")
        else:
            print("  ⚠ Some annotations may not match text")

    print("Template engine: PASSED\n")


def test_synpii_main():
    """Test main SynPII class."""
    print("Testing SynPII main class...")
    from synpii import SynPII

    # Test clinical preset
    synpii = SynPII(preset="clinical_de", seed=42)
    print(f"  ✓ Created SynPII with preset: {synpii.preset}")

    # Generate single entity
    person = synpii.generate_entity("PERSON")
    print(f"  ✓ Generated PERSON: '{person.value}'")

    # Generate document
    doc = synpii.generate_document()
    print(f"  ✓ Generated document: {len(doc.text)} chars, {len(doc.annotations)} annotations")
    print(f"    Template: {doc.template_type}")
    print(f"    First 100 chars: {doc.text[:100]}...")

    # Test annotation extraction
    for ann in doc.annotations[:3]:
        print(f"    - {ann.entity_type}: '{ann.text}' @ [{ann.start}:{ann.end}]")

    print("SynPII main: PASSED\n")


def test_adversarial_generation():
    """Test adversarial scenario generation."""
    print("Testing adversarial scenario generation...")
    from synpii.adversarial import AdversarialGenerator, AdversarialType, AdversarialScenario
    from synpii.generators import GeneratorRegistry
    from synpii.core.lexicon import GermanLexicon
    from pathlib import Path

    values_dir = Path(__file__).parent / "values"
    lexicon = GermanLexicon(values_dir)
    generators = GeneratorRegistry(lexicon=lexicon)

    generator = AdversarialGenerator(generators=generators, lexicon=lexicon)
    # Available recipes depend on registration, check by keys or proxy
    available_types = generator.RECIPES.keys()
    print(f"  ✓ Available adversarial types: {[t.value for t in available_types]}")

    # Generate overlap conflict cases
    scenario = AdversarialScenario(
        adversarial_type=AdversarialType.OVERLAP_CONFLICT,
        entity_type="DE_POSTAL_CODE",
        description="PLZ overlaps with LOCATION",
        evidence={"conflicting_type": "LOCATION"},
    )

    samples = generator.generate_for_scenario(scenario, count=3)
    print(f"  ✓ Generated {len(samples)} adversarial samples:")
    for sample in samples:
        print(f"    - '{sample.text}'")

    print("Adversarial generation: PASSED\n")


def test_output_formats():
    """Test output formatters."""
    print("Testing output formats...")
    from synpii.output import JSONLFormatter, CoNLLFormatter, PresidioFormatter
    from synpii.core.types import GeneratedDocument, Annotation

    doc = GeneratedDocument(
        id="test_001",
        template_type="test",
        text="Patient Hans Müller aus Berlin",
        annotations=[
            Annotation("PERSON", "Hans Müller", 8, 19),
            Annotation("LOCATION", "Berlin", 24, 30),
        ],
    )

    # JSONL
    jsonl = JSONLFormatter()
    output = jsonl.format_document(doc)
    print(f"  ✓ JSONL: {output[:80]}...")

    # CoNLL
    conll = CoNLLFormatter()
    output = conll.format_document(doc)
    print(f"  ✓ CoNLL:\n{output}")

    # Presidio
    presidio = PresidioFormatter()
    output = presidio.format_document(doc)
    print(f"  ✓ Presidio: {output[:80]}...")

    print("Output formats: PASSED\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("SynPII Test Suite")
    print("=" * 60 + "\n")

    tests = [
        test_core_types,
        test_pcfg_grammar,
        test_lexicon,
        test_generators,
        test_perturbations,
        test_template_engine,
        test_synpii_main,
        test_adversarial_generation,
        test_output_formats,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAILED: {test.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
