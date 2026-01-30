"""Contact information generators (phone, email)."""

import random
from typing import Optional

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class PhoneGenerator(BaseGenerator):
    """Generate German phone numbers.

    Supports:
    - Landline with area codes
    - Mobile numbers
    - Multiple format variants
    """

    entity_types = ["PHONE_NUMBER"]

    # German area codes for major cities
    AREA_CODES = [
        "030",   # Berlin
        "040",   # Hamburg
        "069",   # Frankfurt
        "089",   # München
        "0221",  # Köln
        "0211",  # Düsseldorf
        "0711",  # Stuttgart
        "0341",  # Leipzig
        "0351",  # Dresden
        "0511",  # Hannover
        "0611",  # Wiesbaden
        "0621",  # Mannheim
        "0721",  # Karlsruhe
        "0911",  # Nürnberg
        "0228",  # Bonn
        "0231",  # Dortmund
        "0201",  # Essen
        "0241",  # Aachen
    ]

    # Mobile prefixes
    MOBILE_PREFIXES = [
        "0151", "0152", "0157", "0160", "0162", "0163",
        "0170", "0171", "0172", "0173", "0174", "0175", "0176", "0177", "0178", "0179",
    ]

    def generate(
        self,
        phone_type: str = None,
        **kwargs,
    ) -> Entity:
        """Generate a German phone number.

        Args:
            phone_type: 'landline', 'mobile', or None for random.
            **kwargs: Additional parameters.

        Returns:
            Entity with phone number.
        """
        if phone_type is None:
            phone_type = random.choice(["landline", "mobile"])

        if phone_type == "mobile":
            return self._generate_mobile()
        else:
            return self._generate_landline()

    def _generate_landline(self) -> Entity:
        """Generate a landline number."""
        area_code = random.choice(self.AREA_CODES)
        # 7 digits for the local number
        local_number = ''.join([str(random.randint(0, 9)) for _ in range(7)])

        # Format: 030 123 4567
        formatted = f"{area_code} {local_number[:3]} {local_number[3:]}"
        compact = f"{area_code}{local_number}"

        # International format
        international = f"+49 {area_code[1:]} {local_number}"

        variants = [
            formatted,
            compact,
            international,
            f"Tel.: {formatted}",
            f"Telefon: {formatted}",
            f"{area_code}/{local_number}",
            f"{area_code}-{local_number}",
        ]

        return Entity(
            entity_type="PHONE_NUMBER",
            value=formatted,
            variants=variants,
            metadata={
                "area_code": area_code,
                "local_number": local_number,
                "phone_type": "landline",
            },
        )

    def _generate_mobile(self) -> Entity:
        """Generate a mobile number."""
        prefix = random.choice(self.MOBILE_PREFIXES)
        # 7 digits for mobile
        number = ''.join([str(random.randint(0, 9)) for _ in range(7)])

        # Format: 0171 123 4567
        formatted = f"{prefix} {number[:3]} {number[3:]}"
        compact = f"{prefix}{number}"

        # International format
        international = f"+49 {prefix[1:]} {number}"

        variants = [
            formatted,
            compact,
            international,
            f"Mobil: {formatted}",
            f"Handy: {formatted}",
            f"{prefix}/{number}",
        ]

        return Entity(
            entity_type="PHONE_NUMBER",
            value=formatted,
            variants=variants,
            metadata={
                "prefix": prefix,
                "number": number,
                "phone_type": "mobile",
            },
        )


class EmailGenerator(BaseGenerator):
    """Generate email addresses.

    Supports:
    - Personal emails based on names
    - Common German email domains
    """

    entity_types = ["EMAIL_ADDRESS"]

    DOMAINS = [
        "gmail.com",
        "web.de",
        "gmx.de",
        "t-online.de",
        "outlook.de",
        "yahoo.de",
        "posteo.de",
        "mailbox.org",
        "freenet.de",
        "arcor.de",
        "aol.de",
        "icloud.com",
    ]

    def generate(
        self,
        name: str = None,
        **kwargs,
    ) -> Entity:
        """Generate an email address.

        Args:
            name: Base name for email (generates from lexicon if not provided).
            **kwargs: Additional parameters.

        Returns:
            Entity with email address.
        """
        if name is None:
            if self.lexicon is not None:
                name = self.lexicon.sample_last_name()
            else:
                name = random.choice([
                    "mueller", "schmidt", "schneider", "fischer", "weber",
                    "meyer", "wagner", "becker", "schulz", "hoffmann",
                ])

        # Normalize name for email
        local_part = self._normalize_for_email(name)

        # Sometimes add numbers
        if random.random() < 0.3:
            local_part += str(random.randint(1, 99))

        domain = random.choice(self.DOMAINS)
        email = f"{local_part}@{domain}"

        variants = [
            email,
            f"E-Mail: {email}",
            f"Mail: {email}",
            f"email: {email}",
        ]

        return Entity(
            entity_type="EMAIL_ADDRESS",
            value=email,
            variants=variants,
            metadata={
                "local_part": local_part,
                "domain": domain,
            },
        )

    def _normalize_for_email(self, name: str) -> str:
        """Normalize a name for use in email address."""
        # Lowercase
        result = name.lower()

        # Replace spaces with dots
        result = result.replace(" ", ".")

        # Replace German umlauts
        replacements = {
            "ä": "ae", "ö": "oe", "ü": "ue",
            "Ä": "ae", "Ö": "oe", "Ü": "ue",
            "ß": "ss",
        }
        for old, new in replacements.items():
            result = result.replace(old, new)

        # Remove any remaining non-ASCII or special characters
        result = ''.join(c for c in result if c.isalnum() or c in '._-')

        return result
