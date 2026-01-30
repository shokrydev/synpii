"""Organization generators for healthcare settings."""

import random
from typing import Optional

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class OrganizationGenerator(BaseGenerator):
    """Generate healthcare organization names.

    Supports:
    - Hospital/clinic names
    - Medical practice names
    - Insurance companies
    """

    entity_types = ["ORGANIZATION"]

    HOSPITAL_SUFFIXES = ["Mitte", "Nord", "Süd", "Ost", "West", "Zentrum", "Campus"]

    # Default hospital patterns if no lexicon
    DEFAULT_HOSPITALS = [
        "Universitätsklinikum",
        "Klinikum",
        "Krankenhaus",
        "Charité",
        "Helios Klinikum",
        "Asklepios Klinik",
        "Vivantes Klinikum",
        "Sana Klinikum",
        "Städtisches Klinikum",
        "Kreiskrankenhaus",
        "Evangelisches Krankenhaus",
        "Katholisches Krankenhaus",
        "St. Elisabeth-Krankenhaus",
        "St. Josef-Krankenhaus",
        "Marienhospital",
    ]

    # Default cities if no lexicon
    DEFAULT_CITIES = [
        "Berlin", "Hamburg", "München", "Köln", "Frankfurt",
        "Stuttgart", "Düsseldorf", "Leipzig", "Dresden", "Hannover",
    ]

    def generate(
        self,
        org_type: str = "hospital",
        city: str = None,
        **kwargs,
    ) -> Entity:
        """Generate an organization name.

        Args:
            org_type: 'hospital', 'practice', or 'insurance'.
            city: Optional city name to include.
            **kwargs: Additional parameters.

        Returns:
            Entity with organization name.
        """
        if org_type == "practice":
            return self._generate_practice(**kwargs)
        elif org_type == "insurance":
            return self._generate_insurance(**kwargs)
        else:
            return self._generate_hospital(city=city, **kwargs)

    def _generate_hospital(self, city: str = None, **kwargs) -> Entity:
        """Generate a hospital/clinic name."""
        # Get hospital base name
        if self.lexicon is not None and self.lexicon.hospitals:
            base = random.choice(self.lexicon.hospitals)
        else:
            base = random.choice(self.DEFAULT_HOSPITALS)

        # Get city
        if city is None:
            if self.lexicon is not None and self.lexicon.cities:
                city, _, _ = random.choice(self.lexicon.cities)
            else:
                city = random.choice(self.DEFAULT_CITIES)

        # Build hospital name
        # Some bases already include city or are complete names
        if "St." in base or "krankenhaus" in base.lower() or "hospital" in base.lower():
            if "Klinikum" in base or "Klinik" in base:
                hospital = f"{base} {city}"
            else:
                hospital = base
        else:
            # Add city and possibly suffix
            suffix = random.choice(self.HOSPITAL_SUFFIXES + ["", ""])
            if suffix:
                hospital = f"{base} {city} {suffix}"
            else:
                hospital = f"{base} {city}"

        hospital = hospital.strip()

        variants = [
            hospital,
            f"im {hospital}",
            f"an das {hospital}",
            f"des {hospital}",
        ]

        return Entity(
            entity_type="ORGANIZATION",
            value=hospital,
            variants=variants,
            metadata={
                "org_type": "hospital",
                "city": city,
            },
        )

    def _generate_practice(self, doctor_name: str = None, **kwargs) -> Entity:
        """Generate a medical practice name."""
        if doctor_name is None:
            if self.lexicon is not None:
                doctor_name = self.lexicon.sample_last_name()
            else:
                doctor_name = random.choice([
                    "Müller", "Schmidt", "Schneider", "Fischer", "Weber",
                    "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
                ])

        patterns = [
            f"Praxis {doctor_name}",
            f"Praxis Dr. {doctor_name}",
            f"Hausarztpraxis {doctor_name}",
            f"Gemeinschaftspraxis {doctor_name}",
            f"Facharztpraxis {doctor_name}",
        ]

        # Occasionally generate MVZ
        if random.random() < 0.2:
            if self.lexicon is not None and self.lexicon.cities:
                city, _, _ = random.choice(self.lexicon.cities)
            else:
                city = random.choice(self.DEFAULT_CITIES)
            practice = f"MVZ {city}"
        else:
            practice = random.choice(patterns)

        return Entity(
            entity_type="ORGANIZATION",
            value=practice,
            variants=[practice],
            metadata={"org_type": "practice"},
        )

    def _generate_insurance(self, **kwargs) -> Entity:
        """Generate an insurance company name."""
        if self.lexicon is not None and self.lexicon.insurance_companies:
            insurance = random.choice(self.lexicon.insurance_companies)
        else:
            insurance = random.choice([
                "AOK", "Techniker Krankenkasse", "TK", "Barmer",
                "DAK-Gesundheit", "IKK classic", "KKH",
            ])

        return Entity(
            entity_type="ORGANIZATION",
            value=insurance,
            variants=[insurance, f"bei der {insurance}", f"versichert bei {insurance}"],
            metadata={"org_type": "insurance"},
        )
