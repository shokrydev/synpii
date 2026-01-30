"""Age generator with German-specific variants."""

import random
from typing import Optional

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class AgeGenerator(BaseGenerator):
    """Generate age references in German clinical text.

    Supports multiple ways ages are expressed in German medical documents:
    - "45-jährig" (adjective form)
    - "45 Jahre alt" (descriptive)
    - "45 J." (abbreviated)
    - "Alter: 45" (labeled)
    """

    entity_types = ["AGE"]

    def generate(
        self,
        min_age: int = 18,
        max_age: int = 95,
        **kwargs,
    ) -> Entity:
        """Generate an age reference.

        Args:
            min_age: Minimum age to generate.
            max_age: Maximum age to generate.
            **kwargs: Additional parameters.

        Returns:
            Entity with age value.
        """
        age = random.randint(min_age, max_age)

        variants = [
            f"{age}-jährig",        # 45-jährig (adjective, singular)
            f"{age}-jährigen",      # 45-jährigen (adjective, inflected)
            f"{age}-jährige",       # 45-jährige (adjective, feminine/plural)
            f"{age} Jahre alt",     # 45 Jahre alt
            f"{age} J.",            # 45 J. (abbreviated)
            f"Alter: {age}",        # Alter: 45
            f"{age} Jahren",        # 45 Jahren (dative)
            str(age),               # Plain number
        ]

        # Add decade descriptions for certain ages
        if age >= 30 and age < 40:
            variants.append("in den Dreißigern")
        elif age >= 40 and age < 50:
            variants.append("in den Vierzigern")
        elif age >= 50 and age < 60:
            variants.append("in den Fünfzigern")
        elif age >= 60 and age < 70:
            variants.append("in den Sechzigern")
        elif age >= 70 and age < 80:
            variants.append("in den Siebzigern")
        elif age >= 80 and age < 90:
            variants.append("in den Achtzigern")
        elif age >= 90:
            variants.append("in den Neunzigern")

        return Entity(
            entity_type="AGE",
            value=f"{age}-jährig",  # Primary form
            variants=variants,
            metadata={"age": age},
        )
