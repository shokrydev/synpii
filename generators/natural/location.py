"""Location generator with PCFG-based German street names."""

import random
from typing import Optional, Tuple

from synpii.core.types import Entity
from synpii.core.grammar import PCFGEngine, create_street_generator
from synpii.generators.base import BaseGenerator


class LocationGenerator(BaseGenerator):
    """Generate German location entities.

    Supports:
    - Street addresses with PCFG-based name generation
    - City names
    - Full addresses (street + PLZ + city)
    """

    entity_types = ["LOCATION"]

    # Street prepositional prefixes for simple generation
    STREET_PREFIXES = [
        "Am", "An der", "An den", "Auf der", "Auf dem", "Im", "In der",
        "Unter den", "Zum", "Zur", "Bei der", "Beim", "Vor dem", "Vor der",
        "Hinter dem", "Hinter der", "Neben der", "Neben dem",
    ]

    STREET_SUFFIXES = [
        "straße", "weg", "allee", "platz", "ring", "gasse", "damm", "ufer",
        "bach", "kanal", "hof", "stieg", "markt", "wall", "kamp", "graben",
    ]

    HOSPITAL_SUFFIXES = ["Mitte", "Nord", "Süd", "Ost", "West", "Zentrum", "Campus"]

    def __init__(self, lexicon=None, use_pcfg: bool = True, **kwargs):
        """Initialize location generator.

        Args:
            lexicon: GermanLexicon for values.
            use_pcfg: Use PCFG for street generation (recommended).
            **kwargs: Additional parameters.
        """
        super().__init__(lexicon, **kwargs)
        self.use_pcfg = use_pcfg
        self._street_generator = None

    @property
    def street_generator(self) -> PCFGEngine:
        """Lazy-load PCFG street generator."""
        if self._street_generator is None:
            self._street_generator = create_street_generator(self.lexicon)
        return self._street_generator

    def generate(
        self,
        location_type: str = "street",
        with_house_number: bool = True,
        **kwargs,
    ) -> Entity:
        """Generate a location entity.

        Args:
            location_type: 'street', 'city', or 'address'.
            with_house_number: Include house number for streets.
            **kwargs: Additional parameters.

        Returns:
            Entity with location value.
        """
        if location_type == "city":
            return self._generate_city(**kwargs)
        elif location_type == "address":
            return self._generate_full_address(**kwargs)
        else:
            return self._generate_street(with_house_number=with_house_number, **kwargs)

    def _generate_street(self, with_house_number: bool = True, **kwargs) -> Entity:
        """Generate a street name."""
        if self.use_pcfg:
            # Use PCFG for realistic street generation
            street_name = self.street_generator.expand("STREET")
            # Clean up spacing (PCFG adds spaces between parts)
            street_name = self._clean_street_name(street_name)
        else:
            # Simple generation
            street_name = self._generate_simple_street()

        # Add house number
        if with_house_number:
            house_number = str(random.randint(1, 200))
            # Occasionally add letter suffix (1a, 5b)
            if random.random() < 0.1:
                house_number += random.choice(["a", "b", "c"])
            full_street = f"{street_name} {house_number}"
        else:
            house_number = None
            full_street = street_name

        variants = [full_street]
        if house_number:
            variants.append(street_name)  # Without number
        variants.append(street_name.replace("straße", "str.").replace("Straße", "Str."))

        return Entity(
            entity_type="LOCATION",
            value=full_street,
            variants=variants,
            metadata={
                "street_name": street_name,
                "house_number": house_number,
                "location_type": "street",
            },
        )

    def _clean_street_name(self, name: str) -> str:
        """Clean up PCFG-generated street name.

        Handles:
        - Removing extra spaces
        - Joining compound parts (e.g., "Goethe straße" -> "Goethestraße")
        - Fixing hyphenated compound names
        """
        # Fix compound hyphens (remove spaces around hyphens in compound names)
        name = name.replace(" - ", "-")

        # Join suffix to name (remove space before suffix)
        for suffix in self.STREET_SUFFIXES:
            name = name.replace(f" {suffix}", suffix)
            name = name.replace(f" {suffix.capitalize()}", suffix.capitalize())
            # Also handle hyphenated suffixes
            name = name.replace(f"-{suffix}", suffix)
            name = name.replace(f"-{suffix.capitalize()}", suffix.capitalize())

        # Handle genitive 's' and 'ens'
        name = name.replace(" s ", "s")
        name = name.replace(" ens ", "ens")
        name = name.replace(" s", "s")  # End of string

        # Clean double spaces
        while "  " in name:
            name = name.replace("  ", " ")

        return name.strip()

    def _generate_simple_street(self) -> str:
        """Generate a simple street name without PCFG."""
        if self.lexicon is not None and self.lexicon.street_names:
            prefix = random.choice(self.lexicon.street_names)
        else:
            prefix = random.choice([
                "Haupt", "Schiller", "Goethe", "Beethoven", "Mozart", "Bach",
                "Park", "Wald", "Berg", "Kirch", "Markt", "Schloss", "Rosen",
                "Linden", "Friedrichs", "Bahnhof", "Garten",
            ])

        if self.lexicon is not None and self.lexicon.street_suffixes:
            suffix = random.choice(self.lexicon.street_suffixes)
        else:
            suffix = random.choice(self.STREET_SUFFIXES)

        return f"{prefix}{suffix}"

    def _generate_city(self, **kwargs) -> Entity:
        """Generate a city name."""
        if self.lexicon is not None and self.lexicon.cities:
            city_name, plz_min, plz_max = random.choice(self.lexicon.cities)
        else:
            city_name = random.choice([
                "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart",
                "Düsseldorf", "Leipzig", "Dresden", "Hannover", "Nürnberg", "Bremen",
            ])

        variants = [
            city_name,
            f"in {city_name}",
            f"aus {city_name}",
            f"nach {city_name}",
        ]

        return Entity(
            entity_type="LOCATION",
            value=city_name,
            variants=variants,
            metadata={"city": city_name, "location_type": "city"},
        )

    def _generate_full_address(self, **kwargs) -> Entity:
        """Generate a full address (street + PLZ + city)."""
        street_entity = self._generate_street(with_house_number=True)

        if self.lexicon is not None and self.lexicon.cities:
            city_name, plz_min, plz_max = random.choice(self.lexicon.cities)
            plz = str(random.randint(int(plz_min), int(plz_max)))
        else:
            city_name = random.choice([
                "Berlin", "Hamburg", "München", "Köln", "Frankfurt",
            ])
            plz = f"{random.randint(10000, 99999)}"

        full_address = f"{street_entity.value}, {plz} {city_name}"

        return Entity(
            entity_type="LOCATION",
            value=full_address,
            variants=[
                full_address,
                f"{street_entity.value}\n{plz} {city_name}",
                street_entity.value,
            ],
            metadata={
                "street": street_entity.value,
                "street_name": street_entity.metadata.get("street_name"),
                "house_number": street_entity.metadata.get("house_number"),
                "plz": plz,
                "city": city_name,
                "location_type": "address",
            },
        )
