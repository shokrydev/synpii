"""Per-weakness-type generation strategies.

Each strategy generates test cases designed to expose a specific
type of detection weakness.
"""

from abc import ABC, abstractmethod
import random
from typing import List, Optional

from synpii.weakness.types import WeaknessType, WeaknessReport, WeaknessTestCase
from synpii.generators.base import GeneratorRegistry
from synpii.core.lexicon import GermanLexicon


class BaseWeaknessStrategy(ABC):
    """Abstract base class for weakness-targeted generation strategies."""

    weakness_type: WeaknessType = None

    def __init__(
        self,
        generators: GeneratorRegistry = None,
        lexicon: GermanLexicon = None,
    ):
        """Initialize strategy.

        Args:
            generators: Entity generator registry.
            lexicon: German lexicon for values.
        """
        self.generators = generators
        self.lexicon = lexicon

    @abstractmethod
    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate test cases for a specific weakness.

        Args:
            weakness: The weakness report to target.
            count: Number of test cases to generate.

        Returns:
            List of WeaknessTestCase objects.
        """
        pass


class OverlapConflictStrategy(BaseWeaknessStrategy):
    """Generate cases where entity types overlap.

    Common overlaps:
    - DE_POSTAL_CODE vs LOCATION (5-digit numbers near city names)
    - PERSON vs LOCATION (street names from person names)
    - DATE_TIME vs other numeric patterns
    """

    weakness_type = WeaknessType.OVERLAP_CONFLICT

    # Known overlap patterns
    OVERLAP_PATTERNS = {
        ("DE_POSTAL_CODE", "LOCATION"): [
            "{plz} {city}",           # "53168 Bonn"
            "{plz}, {city}",          # "53168, Bonn"
            "PLZ {plz} in {city}",    # Explicit marker
            "{city}, PLZ: {plz}",
            "Postleitzahl {plz}",
        ],
        ("PERSON", "LOCATION"): [
            "{person}straße",         # "Goethestraße" (is it person or location?)
            "{person}platz",
            "Straße {person}",        # "Straße des 17. Juni" pattern
        ],
        ("DATE_TIME", "PHONE_NUMBER"): [
            "01.{num}",               # Date or phone prefix?
        ],
    }

    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate overlap conflict test cases."""
        test_cases = []

        entity_type = weakness.entity_type
        conflicting_type = weakness.evidence.get("conflicting_type")

        # Find relevant patterns
        patterns = []
        for (type1, type2), p_list in self.OVERLAP_PATTERNS.items():
            if entity_type in (type1, type2):
                patterns.extend(p_list)

        if not patterns:
            # Default to PLZ/LOCATION overlap
            patterns = self.OVERLAP_PATTERNS.get(
                ("DE_POSTAL_CODE", "LOCATION"),
                ["{plz} {city}"]
            )

        for i in range(count):
            pattern = random.choice(patterns)
            text, entities = self._generate_from_pattern(pattern, entity_type)
            test_cases.append(WeaknessTestCase(
                text=text,
                expected_entities=entities,
                weakness_type=self.weakness_type,
                difficulty=3,
                metadata={"pattern": pattern},
            ))

        return test_cases

    def _generate_from_pattern(
        self,
        pattern: str,
        primary_type: str,
    ) -> tuple:
        """Generate text from pattern with entity tracking."""
        text = pattern
        entities = []

        # Generate values and track positions
        if "{plz}" in pattern:
            if self.generators and self.generators.is_available("DE_POSTAL_CODE"):
                plz_entity = self.generators.generate("DE_POSTAL_CODE")
                plz = plz_entity.value.split()[0]  # Just the number
            else:
                plz = str(random.randint(10000, 99999))
            text = text.replace("{plz}", plz)
            start = text.find(plz)
            if start >= 0:
                entities.append({
                    "type": "DE_POSTAL_CODE",
                    "text": plz,
                    "start": start,
                    "end": start + len(plz),
                })

        if "{city}" in pattern:
            if self.lexicon and self.lexicon.cities:
                city, _, _ = random.choice(self.lexicon.cities)
            else:
                city = random.choice(["Berlin", "Hamburg", "München", "Köln"])
            text = text.replace("{city}", city)
            start = text.find(city)
            if start >= 0:
                entities.append({
                    "type": "LOCATION",
                    "text": city,
                    "start": start,
                    "end": start + len(city),
                })

        if "{person}" in pattern:
            if self.generators and self.generators.is_available("PERSON"):
                person_entity = self.generators.generate("PERSON")
                name = person_entity.metadata.get("last_name", person_entity.value.split()[-1])
            else:
                name = random.choice(["Goethe", "Schiller", "Bach", "Mozart"])
            text = text.replace("{person}", name)

        if "{num}" in pattern:
            num = f"{random.randint(1, 12):02d}.{random.randint(2020, 2024)}"
            text = text.replace("{num}", num)

        return text, entities


class FormatVariationStrategy(BaseWeaknessStrategy):
    """Generate cases with unusual entity formats.

    Tests detection robustness against:
    - Alternative delimiters
    - Missing/extra spaces
    - Different date formats
    - Abbreviated forms
    """

    weakness_type = WeaknessType.FORMAT_VARIATION

    FORMAT_VARIATIONS = {
        "DATE_TIME": [
            ("standard", "{d:02d}.{m:02d}.{y}"),        # 15.03.1990
            ("no_leading_zero", "{d}.{m}.{y}"),         # 15.3.1990
            ("slash", "{d:02d}/{m:02d}/{y}"),           # 15/03/1990
            ("dash", "{d:02d}-{m:02d}-{y}"),            # 15-03-1990
            ("text_month", "{d}. {month} {y}"),         # 15. März 1990
            ("iso", "{y}-{m:02d}-{d:02d}"),             # 1990-03-15
        ],
        "PHONE_NUMBER": [
            ("standard", "{area} {n1} {n2}"),           # 030 123 4567
            ("compact", "{area}{num}"),                  # 0301234567
            ("dashes", "{area}-{n1}-{n2}"),             # 030-123-4567
            ("international", "+49 {area_short} {num}"), # +49 30 1234567
            ("parentheses", "({area}) {num}"),           # (030) 1234567
        ],
        "DE_KVNR": [
            ("standard", "{kvnr}"),                      # A123456780
            ("labeled", "KVNR: {kvnr}"),                # KVNR: A123456780
            ("spaced", "{letter} {digits}"),            # A 123456780
        ],
    }

    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate format variation test cases."""
        test_cases = []

        entity_type = weakness.entity_type
        variations = self.FORMAT_VARIATIONS.get(entity_type, [])

        if not variations:
            return test_cases

        for i in range(count):
            var_name, var_pattern = random.choice(variations)
            text, entities = self._generate_variation(entity_type, var_pattern)

            test_cases.append(WeaknessTestCase(
                text=text,
                expected_entities=entities,
                weakness_type=self.weakness_type,
                difficulty=2 if var_name == "standard" else 4,
                metadata={"variation": var_name},
            ))

        return test_cases

    def _generate_variation(
        self,
        entity_type: str,
        pattern: str,
    ) -> tuple:
        """Generate a single variation."""
        text = pattern
        entities = []

        if entity_type == "DATE_TIME":
            d, m, y = random.randint(1, 28), random.randint(1, 12), random.randint(1950, 2024)
            months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                      "Juli", "August", "September", "Oktober", "November", "Dezember"]
            text = pattern.format(d=d, m=m, y=y, month=months[m-1])

        elif entity_type == "PHONE_NUMBER":
            area = random.choice(["030", "040", "069", "089", "0221"])
            num = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            text = pattern.format(
                area=area,
                area_short=area[1:],
                num=num,
                n1=num[:3],
                n2=num[3:],
            )

        elif entity_type == "DE_KVNR":
            letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            kvnr = letter + digits
            text = pattern.format(kvnr=kvnr, letter=letter, digits=digits)

        entities.append({
            "type": entity_type,
            "text": text,
            "start": 0,
            "end": len(text),
        })

        return text, entities


class ContextDependencyStrategy(BaseWeaknessStrategy):
    """Generate cases testing context-dependent detection.

    Tests whether detection requires specific context words
    (e.g., "KVNR:", "geb.", "Tel.") to recognize entities.
    """

    weakness_type = WeaknessType.CONTEXT_DEPENDENCY

    CONTEXT_PATTERNS = {
        "DE_KVNR": [
            ("with_label", "Versichertennummer: {value}"),
            ("with_abbr", "KVNR: {value}"),
            ("no_context", "{value}"),
            ("sentence", "Die Versichertennummer lautet {value}"),
        ],
        "DATE_TIME": [
            ("with_label", "Geburtsdatum: {value}"),
            ("with_geb", "geb. {value}"),
            ("no_context", "{value}"),
            ("sentence", "Der Patient wurde am {value} geboren"),
        ],
        "PHONE_NUMBER": [
            ("with_label", "Telefon: {value}"),
            ("with_abbr", "Tel.: {value}"),
            ("no_context", "{value}"),
            ("sentence", "Erreichbar unter {value}"),
        ],
    }

    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate context dependency test cases."""
        test_cases = []

        entity_type = weakness.entity_type
        patterns = self.CONTEXT_PATTERNS.get(entity_type, [])

        if not patterns and self.generators:
            # Default: test with and without generic context
            patterns = [
                ("no_context", "{value}"),
                ("generic", "Der Wert ist {value}"),
            ]

        for i in range(count):
            context_type, pattern = random.choice(patterns)

            # Generate entity value
            if self.generators and self.generators.is_available(entity_type):
                entity = self.generators.generate(entity_type)
                value = entity.value
            else:
                value = f"[{entity_type}]"

            text = pattern.format(value=value)
            start = text.find(value)

            test_cases.append(WeaknessTestCase(
                text=text,
                expected_entities=[{
                    "type": entity_type,
                    "text": value,
                    "start": start,
                    "end": start + len(value),
                }],
                weakness_type=self.weakness_type,
                difficulty=2 if context_type != "no_context" else 5,
                metadata={"context_type": context_type},
            ))

        return test_cases


class CoverageGapStrategy(BaseWeaknessStrategy):
    """Generate cases for entity types with no recognizer coverage."""

    weakness_type = WeaknessType.COVERAGE_GAP

    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate coverage gap test cases."""
        test_cases = []
        entity_type = weakness.entity_type

        for i in range(count):
            if self.generators and self.generators.is_available(entity_type):
                entity = self.generators.generate(entity_type)
                value = entity.value
            else:
                value = f"[{entity_type}_example_{i}]"

            text = f"Der Wert {value} sollte erkannt werden."
            start = text.find(value)

            test_cases.append(WeaknessTestCase(
                text=text,
                expected_entities=[{
                    "type": entity_type,
                    "text": value,
                    "start": start,
                    "end": start + len(value),
                }],
                weakness_type=self.weakness_type,
                difficulty=5,
                metadata={"note": "No recognizer available"},
            ))

        return test_cases


class EntityConfusionStrategy(BaseWeaknessStrategy):
    """Generate cases where entity types are commonly confused."""

    weakness_type = WeaknessType.ENTITY_CONFUSION

    # Common confusion pairs
    CONFUSION_PAIRS = [
        ("PERSON", "ORGANIZATION"),     # "Dr. Müller" vs "Praxis Müller"
        ("LOCATION", "ORGANIZATION"),   # "Charité" (hospital vs location)
        ("DE_POSTAL_CODE", "AGE"),       # 5-digit numbers
    ]

    def generate(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate entity confusion test cases."""
        test_cases = []
        entity_type = weakness.entity_type
        confused_type = weakness.evidence.get("confused_with")

        for i in range(count):
            # Generate ambiguous text
            if entity_type == "PERSON" and self.lexicon:
                # Names that look like organizations
                name = self.lexicon.sample_last_name()
                patterns = [
                    f"Dr. {name}",      # Person
                    f"Praxis {name}",   # Organization
                    f"{name} GmbH",     # Organization
                ]
                pattern = random.choice(patterns)
                expected_type = "PERSON" if pattern.startswith("Dr.") else "ORGANIZATION"
            else:
                if self.generators and self.generators.is_available(entity_type):
                    entity = self.generators.generate(entity_type)
                    pattern = entity.value
                    expected_type = entity_type
                else:
                    pattern = f"[{entity_type}]"
                    expected_type = entity_type

            test_cases.append(WeaknessTestCase(
                text=pattern,
                expected_entities=[{
                    "type": expected_type,
                    "text": pattern,
                    "start": 0,
                    "end": len(pattern),
                }],
                weakness_type=self.weakness_type,
                difficulty=4,
                metadata={"confusion_pair": (entity_type, confused_type)},
            ))

        return test_cases
