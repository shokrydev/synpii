"""Person name generator with German name patterns."""

import random
from typing import List, Optional

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class PersonGenerator(BaseGenerator):
    """Generate realistic German person names.

    Supports:
    - Male/female names
    - Titles (Dr., Prof., etc.)
    - Multiple variants (formal, informal, abbreviated)
    """

    entity_types = ["PERSON"]

    TITLES = ["Dr.", "Dr. med.", "Prof.", "Prof. Dr.", "PD Dr."]
    MEDICAL_TITLES = ["Dr.", "Dr. med.", "Prof. Dr.", "PD Dr.", "OA", "CA"]

    def generate(
        self,
        gender: str = None,
        with_title: bool = False,
        title_type: str = "general",
        **kwargs,
    ) -> Entity:
        """Generate a person name.

        Args:
            gender: 'male', 'female', or None for random.
            with_title: Include a title (Dr., Prof., etc.).
            title_type: 'general', 'medical', or specific title.
            **kwargs: Additional parameters.

        Returns:
            Entity with person name.
        """
        if gender is None:
            gender = random.choice(["male", "female"])

        # Get first name
        if self.lexicon is not None:
            first_name = self.lexicon.sample_first_name(gender)
            last_name = self.lexicon.sample_last_name()
        else:
            # Fallback names
            if gender == "male":
                first_name = random.choice([
                    "Hans", "Peter", "Michael", "Thomas", "Andreas", "Stefan",
                    "Wolfgang", "Klaus", "Martin", "Matthias", "Christian",
                ])
            else:
                first_name = random.choice([
                    "Maria", "Anna", "Elisabeth", "Monika", "Petra", "Sabine",
                    "Christine", "Julia", "Laura", "Sarah", "Sophie",
                ])
            last_name = random.choice([
                "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
                "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Richter",
            ])

        full_name = f"{first_name} {last_name}"

        # Build variants
        title_prefix = ""
        if gender == "male":
            salutation = "Herr"
            salutation_abbr = "Hr."
        else:
            salutation = "Frau"
            salutation_abbr = "Fr."

        variants = [
            full_name,
            f"{salutation} {last_name}",
            f"{salutation_abbr} {last_name}",
            last_name,
            f"{first_name[0]}. {last_name}",
        ]

        # Add title if requested
        if with_title:
            if title_type == "medical":
                title = random.choice(self.MEDICAL_TITLES)
            elif title_type in self.TITLES:
                title = title_type
            else:
                title = random.choice(self.TITLES)

            title_prefix = title
            titled_name = f"{title} {full_name}"
            variants.insert(0, titled_name)
            variants.append(f"{title} {last_name}")

        return Entity(
            entity_type="PERSON",
            value=variants[0],  # Primary value (with title if applicable)
            variants=variants,
            metadata={
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "title": title_prefix if with_title else None,
            },
        )

    def generate_doctor(self, **kwargs) -> Entity:
        """Convenience method to generate a doctor name."""
        return self.generate(with_title=True, title_type="medical", **kwargs)

    def generate_patient_reference(self, entity: Entity) -> str:
        """Generate a patient reference (Herr/Frau + last name).

        This is NOT PII itself - just a reference form.

        Args:
            entity: Person entity to reference.

        Returns:
            Reference string like "Herr Müller".
        """
        gender = entity.metadata.get("gender", "male")
        last_name = entity.metadata.get("last_name", entity.value.split()[-1])
        salutation = "Herr" if gender == "male" else "Frau"
        return f"{salutation} {last_name}"
