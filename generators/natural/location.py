"""Location generator with German street names."""

import random
from typing import Optional, Tuple

from synpii.core.types import Entity
from synpii.core.grammar import GermanStreetGenerator
from synpii.generators.base import BaseGenerator


class LocationGenerator(BaseGenerator):
    """Generate German location entities.

    Supports:
    - Street addresses with proper compound word formation
    - City names
    - Full addresses (street + PLZ + city)
    """

    entity_types = ["LOCATION"]

    STREET_SUFFIXES = [
        "straße", "weg", "allee", "platz", "ring", "gasse", "damm", "ufer",
        "bach", "kanal", "hof", "stieg", "markt", "wall", "kamp", "graben",
    ]

    HOSPITAL_SUFFIXES = ["Mitte", "Nord", "Süd", "Ost", "West", "Zentrum", "Campus"]

    def __init__(self, lexicon=None, **kwargs):
        """Initialize location generator.

        Args:
            lexicon: GermanLexicon for values.
            **kwargs: Additional parameters.
        """
        super().__init__(lexicon, **kwargs)
        self._street_generator = None

    @property
    def street_generator(self) -> GermanStreetGenerator:
        """Lazy-load street generator."""
        if self._street_generator is None:
            self._street_generator = GermanStreetGenerator(self.lexicon)
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
        # Use the specialized German street generator
        street_name = self.street_generator.generate()

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
        # Add abbreviated variant
        abbrev = street_name.replace("straße", "str.").replace("Straße", "Str.")
        if abbrev != street_name:
            variants.append(abbrev if not house_number else f"{abbrev} {house_number}")

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
