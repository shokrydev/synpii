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
    2. Create 11-digit number: [2 letter digits] + [8 random] + [check]
    3. Apply weights 1,2,1,2,... and sum cross-sums
    4. total % 10 must equal the check digit
    """

    entity_types = ["DE_KVNR"]

    def generate(self, **kwargs) -> Entity:
        """Generate a valid KVNR."""
        letter = random.choice(string.ascii_uppercase)
        digits = [random.randint(0, 9) for _ in range(8)]

        letter_num = ord(letter) - ord('A') + 1
        all_digits = [letter_num // 10, letter_num % 10] + digits

        def cross_sum(n):
            return sum(int(d) for d in str(n))

        total = 0
        for i, d in enumerate(all_digits):
            weight = 2 if i % 2 == 1 else 1
            total += cross_sum(d * weight)

        # Adjust last digit to make total % 10 == 0
        remainder = total % 10
        if remainder != 0:
            old_contrib = cross_sum(digits[7] * 2)
            for new_d in range(10):
                new_contrib = cross_sum(new_d * 2)
                if (total - old_contrib + new_contrib) % 10 == 0:
                    digits[7] = new_d
                    break

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
