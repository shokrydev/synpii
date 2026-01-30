"""German postal code generator."""

import random
from typing import Optional, Tuple

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class PostalCodeGenerator(BaseGenerator):
    """Generate German postal codes (PLZ).

    German postal codes are 5-digit numbers. This generator
    can produce:
    - Random valid PLZ
    - PLZ matching a specific city
    - PLZ with associated city name
    """

    entity_types = ["DE_POSTAL_CODE"]

    def generate(
        self,
        city: str = None,
        include_city: bool = False,
        **kwargs,
    ) -> Entity:
        """Generate a German postal code.

        Args:
            city: Specific city to match (uses lexicon).
            include_city: Include city name in primary value.
            **kwargs: Additional parameters.

        Returns:
            Entity with PLZ value.
        """
        city_name = None
        plz = None

        # Try to get city from lexicon
        if self.lexicon is not None and self.lexicon.cities:
            if city:
                # Find matching city
                for c_name, c_min, c_max in self.lexicon.cities:
                    if c_name.lower() == city.lower():
                        plz = str(random.randint(int(c_min), int(c_max)))
                        city_name = c_name
                        break

            if plz is None:
                # Random city
                city_name, plz_min, plz_max = random.choice(self.lexicon.cities)
                plz = str(random.randint(int(plz_min), int(plz_max)))
        else:
            # No lexicon - generate random valid PLZ
            # German PLZ range: 01001-99998
            plz = f"{random.randint(1001, 99998):05d}"

        # Build value
        if include_city and city_name:
            value = f"{plz} {city_name}"
        else:
            value = plz

        # Build variants
        variants = [plz]
        if city_name:
            variants.extend([
                f"{plz} {city_name}",
                f"PLZ {plz}",
                f"{plz}, {city_name}",
            ])
        else:
            variants.append(f"PLZ {plz}")

        return Entity(
            entity_type="DE_POSTAL_CODE",
            value=value,
            variants=variants,
            metadata={"plz": plz, "city": city_name} if city_name else {"plz": plz},
        )
