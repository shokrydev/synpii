"""Financial identifier generators (IBAN, etc.)."""

import random
import string

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class IBANGenerator(BaseGenerator):
    """Generate valid German IBAN (International Bank Account Number).

    German IBAN format: DE[CHECK][BLZ][ACCOUNT]
    - DE: Country code
    - CHECK: 2-digit check digits (ISO 7064 mod 97)
    - BLZ: 8-digit bank code (Bankleitzahl)
    - ACCOUNT: 10-digit account number

    Total length: 22 characters
    """

    entity_types = ["IBAN"]

    # Common German bank codes (BLZ)
    COMMON_BLZ = [
        "10010010",  # Postbank
        "10020500",  # Bank für Sozialwirtschaft
        "10050000",  # Landesbank Berlin
        "10070000",  # Deutsche Bank Berlin
        "10070024",  # Deutsche Bank PGK Berlin
        "10090000",  # Berliner Volksbank
        "20050550",  # Hamburger Sparkasse
        "30050000",  # Landesbank Hessen-Thüringen
        "37040044",  # Commerzbank Köln
        "50010517",  # ING-DiBa
        "50050201",  # Frankfurter Sparkasse
        "50070010",  # Deutsche Bank Frankfurt
        "50070024",  # Deutsche Bank PGK Frankfurt
        "50090500",  # Sparda-Bank Hessen
        "60050101",  # BW-Bank
        "70010080",  # Postbank München
        "70020270",  # HypoVereinsbank
        "70050000",  # Bayerische Landesbank
        "76050101",  # Sparkasse Nürnberg
        "86050200",  # Stadtsparkasse Dresden
    ]

    def _calculate_check_digits(self, blz: str, account: str) -> str:
        """Calculate IBAN check digits using ISO 7064 mod 97.

        Algorithm:
        1. Construct BBAN: BLZ + ACCOUNT
        2. Move country code to end: BBAN + "DE00"
        3. Replace letters with digits (A=10, B=11, ..., Z=35)
        4. Calculate: 98 - (number mod 97)
        """
        # Construct provisional IBAN with 00 as check digits
        # Then compute: BBAN + "DE00" as number
        bban = blz + account

        # Convert to numeric string (DE = 13 14, then 00)
        numeric_str = bban + "131400"

        # Calculate check digits
        remainder = int(numeric_str) % 97
        check_digits = 98 - remainder

        return f"{check_digits:02d}"

    def generate(self, **kwargs) -> Entity:
        """Generate a valid German IBAN."""
        blz = random.choice(self.COMMON_BLZ)
        account = f"{random.randint(0, 9999999999):010d}"

        check_digits = self._calculate_check_digits(blz, account)
        iban = f"DE{check_digits}{blz}{account}"

        # Format with spaces for readability
        iban_formatted = " ".join([
            iban[0:4], iban[4:8], iban[8:12], iban[12:16], iban[16:20], iban[20:22]
        ])

        return Entity(
            entity_type="IBAN",
            value=iban,
            variants=[
                iban,
                iban_formatted,
                f"IBAN: {iban}",
                f"IBAN: {iban_formatted}",
            ],
            metadata={"blz": blz, "account": account},
        )
