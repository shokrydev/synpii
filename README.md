# SynPII

Grammar-aware synthetic PII generation for German clinical text. Built for benchmarking PII detection systems and researching anonymization weaknesses.

## Features

- **German Grammar Awareness**: Proper gender/case agreement (der/die/das, dative articles)
- **PCFG Street Generation**: 9 pattern families for realistic German addresses (Goethestraße, Am Markt, Straße des 17. Juni)
- **Presidio-Compatible Checksums**: All generated identifiers pass Presidio validation (KVNR, LANR, Tax ID, etc.)
- **Temporal Consistency**: Birth dates match ages, admission before discharge
- **Adversarial Perturbations**: OCR noise, BPE tokenization traps, grammar corruption
- **Weakness-Targeted Generation**: Generate test cases that expose specific detection weaknesses
- **Zipfian Frequency Distribution**: Common names/cities appear more frequently

## Quick Start

```python
from synpii import SynPII

# Create generator with clinical preset
synpii = SynPII(preset="clinical_de", seed=42)

# Generate a single entity
person = synpii.generate_entity("PERSON")
print(person.value)  # "Hans Müller"
print(person.variants)  # ["Hans Müller", "Herr Müller", "H. Müller"]

# Generate a full document with annotations
doc = synpii.generate_document()
print(doc.text[:100])
for ann in doc.annotations:
    print(f"  {ann.entity_type}: '{ann.text}' @ [{ann.start}:{ann.end}]")
```

## Supported Entity Types

### Healthcare Identifiers
- `DE_KVNR` - Patient health insurance number (valid checksums)
- `DE_LANR` - Physician identifier
- `DE_BSNR` - Healthcare facility ID
- `DE_TELEMATIK_ID` - Digital health ID

### Government Identifiers
- `DE_TAX_ID` - Tax identification number (ISO 7064 MOD 11,10)
- `DE_PERSONAL_ID` - Personal ID card number
- `DE_SOCIAL_SECURITY` - Social security number
- `DE_PASSPORT` - Passport number
- `DE_DRIVER_LICENSE` - Driver's license
- `DE_LICENSE_PLATE` - Vehicle license plate

### Natural Language
- `PERSON` - German names with gender-appropriate variants
- `LOCATION` - Addresses with proper compound word formation
- `DATE_TIME` - German date formats (DD.MM.YYYY)
- `PHONE_NUMBER` - German phone formats
- `EMAIL_ADDRESS` - Email addresses
- `AGE` - Age expressions (67-jährig, 67 Jahre alt)

### Financial
- `IBAN` - Valid German IBANs
- `DE_POSTAL_CODE` - 5-digit postal codes

## Template System

Templates use `{{entity_type}}` or `{{entity_type:name}}` placeholders:

```
Patient: {{PERSON:patient}}
Geburtsdatum: {{DATE_TIME:birth}}
Versichertennummer: {{DE_KVNR}}

Der {{non_pii:age_ref}} {{PERSON:patient_ref}} wurde am {{DATE_TIME:admission}}
stationär aufgenommen.
```

Named placeholders can be referenced later (e.g., `patient` → `patient_ref` for "Herr Müller").

## Perturbation Pipeline

Apply realistic noise to test detection robustness:

```python
from synpii.perturbations import OCRPerturbation, BPEPerturbation, GrammarCorruption

# OCR scanning errors
ocr = OCRPerturbation(probability=0.3)
ocr.apply("Goethestraße 10")  # "6oethestrasse I0"

# BPE tokenization artifacts
bpe = BPEPerturbation(probability=0.5)
bpe.apply("Goethestraße")  # "Goethe-straße"

# Grammar corruption
grammar = GrammarCorruption(probability=0.3)
grammar.apply("an der Brücke")  # "an Brücke"
```

## Weakness-Targeted Generation

Generate test cases that expose specific detection weaknesses:

```python
from synpii.weakness import WeaknessTargetedGenerator, WeaknessType, WeaknessReport

targeted = WeaknessTargetedGenerator(generators=registry, lexicon=lexicon)

# Generate cases where PLZ overlaps with LOCATION
weakness = WeaknessReport(
    weakness_type=WeaknessType.OVERLAP_CONFLICT,
    entity_type="DE_POSTAL_CODE",
    description="PLZ overlaps with LOCATION",
    evidence={"conflicting_type": "LOCATION"},
)

cases = targeted.generate_for_weakness(weakness, count=10)
```

Weakness types:
- `OVERLAP_CONFLICT` - Entity boundaries overlap with other types
- `FORMAT_VARIATION` - Non-standard format variations
- `CONTEXT_DEPENDENCY` - Requires specific context words
- `COVERAGE_GAP` - No recognizer handles this type
- `ENTITY_CONFUSION` - Wrong entity type assigned

## Output Formats

```python
from synpii.output import JSONLFormatter, CoNLLFormatter, PresidioFormatter

# JSONL (for training data)
jsonl = JSONLFormatter()
print(jsonl.format_document(doc))

# CoNLL (BIO tags)
conll = CoNLLFormatter()
print(conll.format_document(doc))

# Presidio format
presidio = PresidioFormatter()
print(presidio.format_document(doc))
```

## Configuration

```python
# Custom configuration
synpii = SynPII(
    preset="clinical_de",
    seed=42,  # Reproducible generation
    perturbation_rate=0.2,  # 20% of entities get perturbed
)

# Disable weighted sampling for uniform distribution
from synpii.core.lexicon import GermanLexicon
lexicon = GermanLexicon(values_dir, use_weighted_sampling=False)
```

## Extending Value Files

Values are stored in plain text files under `synpii/values/`:

```
values/
├── names/
│   ├── first_names_male.txt
│   ├── first_names_female.txt
│   └── last_names.txt
├── locations/
│   ├── cities.txt           # Berlin|10115|14199
│   ├── street_names.txt
│   └── nouns_with_gender.txt # Wald|m|0.15
└── clinical/
    ├── diagnoses.txt
    └── medications.txt
```

Files at the top are sampled more frequently (Zipfian distribution).

## Integration with PIIgent

SynPII is designed for integration with the PIIgent Weakness Analyzer:

```python
from synpii import SynPII
from synpii.weakness import WeaknessTargetedGenerator

class WeaknessAnalyzer:
    def __init__(self):
        self.synpii = SynPII(preset="clinical_de")
        self.targeted_gen = WeaknessTargetedGenerator(
            generators=self.synpii.generators,
            lexicon=self.synpii.lexicon,
        )

    def generate_exploration_data(self, weakness):
        return self.targeted_gen.generate_for_weakness(weakness, count=50)
```

## Development

```bash
# Run tests
python -m synpii.test_synpii

# Validate checksums against Presidio
python -m synpii.test_checksums
```
