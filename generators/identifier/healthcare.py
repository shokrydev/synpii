"""German healthcare identifier generators.

Implements generators for:
- KVNR (Krankenversichertennummer) - Patient health insurance ID
- LANR (Lebenslange Arztnummer) - Physician identifier
- BSNR (Betriebsstättennummer) - Healthcare facility ID
- Telematik-ID - Digital health identifier

All generators produce valid identifiers with correct checksums.
"""

import random
import string
from typing import List

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class KVNRGenerator(BaseGenerator):
    """Generate valid KVNR (Krankenversichertennummer).

    Format: [A-Z][0-9]{9} with modified Luhn checksum.

    The checksum algorithm (per §290 SGB V):
    1. Convert letter to 2-digit number (A=01...Z=26)
    2. Create 11-digit number: [2 letter digits] + [8 random digits] + [check]
    3. Apply weights 1,2,1,2,... and sum cross-sums of products
    4. The sum (including check digit) modulo 10 must equal check digit

    This requires the partial sum (without check digit) to be divisible by 10.
    """

    entity_types = ["DE_KVNR"]

    # Cross-sum of d*2 for d in 0-9
    CROSS_SUMS_WEIGHT2 = [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]

    @staticmethod
    def _cross_sum(n: int) -> int:
        """Calculate cross-sum (digit sum) of a number."""
        return sum(int(d) for d in str(n))

    def generate(self, **kwargs) -> Entity:
        """Generate a valid KVNR."""
        letter = random.choice(string.ascii_uppercase)

        # Generate first 7 random digits
        digits = [random.randint(0, 9) for _ in range(7)]

        # Convert letter to 2-digit number (A=01, B=02, ..., Z=26)
        letter_num = ord(letter) - ord('A') + 1

        # Calculate partial sum for first 9 positions
        # Positions: 0=letter_tens, 1=letter_ones, 2-8=digits[0-6]
        # Weights:   1,           2,             1,2,1,2,1,2,1
        partial_sum = 0
        partial_sum += self._cross_sum((letter_num // 10) * 1)  # pos 0
        partial_sum += self._cross_sum((letter_num % 10) * 2)   # pos 1
        for i, d in enumerate(digits):  # pos 2-8
            weight = 2 if (i + 2) % 2 == 1 else 1
            partial_sum += self._cross_sum(d * weight)

        # Position 9 has weight 2. Find digit that makes total sum % 10 == 0
        needed = (10 - partial_sum % 10) % 10
        # Find d8 such that cross_sum(d8 * 2) == needed
        d8 = self.CROSS_SUMS_WEIGHT2.index(needed)
        digits.append(d8)

        # Now S10 % 10 == 0, so any check digit D satisfies (S10 + D) % 10 == D
        # By convention, set check digit to 0 (or we could use total % 10)
        check_digit = 0

        kvnr = letter + ''.join(map(str, digits)) + str(check_digit)

        return Entity(
            entity_type="DE_KVNR",
            value=kvnr,
            variants=[
                kvnr,
                f"KVNR: {kvnr}",
                f"Versichertennummer {kvnr}",
                f"VersNr.: {kvnr}",
            ],
            metadata={"letter": letter},
        )


class LANRGenerator(BaseGenerator):
    """Generate valid LANR (Lebenslange Arztnummer).

    Format: [0-9]{9} with KBV checksum.

    Structure:
    - Positions 1-2: KV region code
    - Positions 3-6: Serial number
    - Position 7: Checksum
    - Positions 8-9: Practice type code
    """

    entity_types = ["DE_LANR"]

    # KV regions (first 2 digits of BSNR/LANR)
    KV_REGIONS = [
        "01", "02", "03", "17", "20", "38", "46", "51",
        "52", "71", "72", "73", "78", "83", "88", "93", "98",
    ]

    def generate(self, **kwargs) -> Entity:
        """Generate a valid LANR."""
        kv_region = random.choice(self.KV_REGIONS)
        base = [random.randint(0, 9) for _ in range(4)]

        first_six = [int(kv_region[0]), int(kv_region[1])] + base
        weights = [4, 9, 4, 9, 4, 9]
        total = sum(d * w for d, w in zip(first_six, weights))
        checksum = (10 - (total % 10)) % 10

        practice_type = f"{random.randint(1, 99):02d}"
        lanr = kv_region + ''.join(map(str, base)) + str(checksum) + practice_type

        return Entity(
            entity_type="DE_LANR",
            value=lanr,
            variants=[
                lanr,
                f"LANR: {lanr}",
                f"Arztnummer {lanr}",
                f"LANR {lanr}",
            ],
            metadata={"kv_region": kv_region, "practice_type": practice_type},
        )


class BSNRGenerator(BaseGenerator):
    """Generate valid BSNR (Betriebsstättennummer).

    Format: [KV_REGION][7_DIGITS]
    - Positions 1-2: KV region code
    - Positions 3-9: Sequence number (no checksum)
    """

    entity_types = ["DE_BSNR"]

    KV_REGIONS = [
        "01", "02", "03", "17", "20", "38", "46", "51",
        "52", "71", "72", "73", "78", "83", "88", "93", "98",
    ]

    def generate(self, **kwargs) -> Entity:
        """Generate a valid BSNR."""
        kv_region = random.choice(self.KV_REGIONS)
        sequence = f"{random.randint(0, 9999999):07d}"
        bsnr = kv_region + sequence

        return Entity(
            entity_type="DE_BSNR",
            value=bsnr,
            variants=[
                bsnr,
                f"BSNR: {bsnr}",
                f"Praxisnummer {bsnr}",
                f"BSNR {bsnr}",
            ],
            metadata={"kv_region": kv_region},
        )


class TelematikIDGenerator(BaseGenerator):
    """Generate Telematik-ID (eGK/eHBA identifier).

    Format: [PREFIX]-[12_DIGITS]

    Prefixes:
    - 1-: eGK (elektronische Gesundheitskarte)
    - 10-: eHBA (elektronischer Heilberufsausweis)
    - 5-2-: SMC-B (Institution card)
    - 9-: KTR-AdV
    - 11-: Alternative Versichertenidentität
    """

    entity_types = ["DE_TELEMATIK_ID"]

    PREFIXES = ["1-", "10-", "5-2-", "9-", "11-"]

    def generate(self, **kwargs) -> Entity:
        """Generate a Telematik-ID."""
        prefix = random.choice(self.PREFIXES)
        identifier = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        telematik_id = prefix + identifier

        return Entity(
            entity_type="DE_TELEMATIK_ID",
            value=telematik_id,
            variants=[
                telematik_id,
                f"Telematik-ID: {telematik_id}",
                f"Telematik-ID {telematik_id}",
            ],
            metadata={"prefix": prefix},
        )
