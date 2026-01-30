"""German government identifier generators.

Implements generators for:
- DE_TAX_ID (Steueridentifikationsnummer)
- DE_PERSONAL_ID (Personalausweisnummer)
- DE_SOCIAL_SECURITY (Sozialversicherungsnummer)
- DE_PASSPORT (Reisepassnummer)
- DE_DRIVER_LICENSE (Führerscheinnummer)
- DE_LICENSE_PLATE (KFZ-Kennzeichen)

All generators produce valid identifiers compatible with Presidio recognizers.
"""

import random
import string
from collections import Counter
from typing import List

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class TaxIDGenerator(BaseGenerator):
    """Generate valid German Tax ID (Steueridentifikationsnummer).

    Format: 11 digits with ISO 7064 MOD 11,10 checksum.

    Rules:
    - First digit is not 0
    - One digit appears exactly 2 or 3 times in first 10 digits
    - At least one digit (0-9) must not appear at all in first 10
    - Last digit is check digit (ISO 7064 MOD 11,10)
    """

    entity_types = ["DE_TAX_ID"]

    def generate(self, **kwargs) -> Entity:
        """Generate a valid German Tax ID."""
        # Generate first 10 digits following distribution rules
        digits = self._generate_valid_digits()

        # Calculate check digit using ISO 7064 MOD 11,10
        check_digit = self._calculate_checksum(digits)
        digits.append(check_digit)

        tax_id = ''.join(map(str, digits))

        return Entity(
            entity_type="DE_TAX_ID",
            value=tax_id,
            variants=[
                tax_id,
                f"{tax_id[:3]} {tax_id[3:6]} {tax_id[6:9]} {tax_id[9:]}",
                f"Steuer-ID: {tax_id}",
                f"IdNr. {tax_id}",
            ],
            metadata={},
        )

    def _generate_valid_digits(self) -> List[int]:
        """Generate 10 digits following Tax ID distribution rules."""
        while True:
            # First digit must not be 0
            digits = [random.randint(1, 9)]
            digits.extend([random.randint(0, 9) for _ in range(9)])

            # Check distribution rules
            counts = Counter(digits)

            # At least one digit must not appear
            if len(counts) == 10:
                continue

            # One digit must appear 2 or 3 times
            count_values = list(counts.values())
            if any(c in (2, 3) for c in count_values):
                return digits

    def _calculate_checksum(self, digits: List[int]) -> int:
        """Calculate ISO 7064 MOD 11,10 check digit."""
        product = 10

        for digit in digits:
            summe = (digit + product) % 10
            if summe == 0:
                summe = 10
            product = (2 * summe) % 11

        check_digit = (11 - product) % 10
        return check_digit


class PersonalIDGenerator(BaseGenerator):
    """Generate valid German Personal ID (Personalausweisnummer).

    Format: 9 or 10 alphanumeric characters with check digit.

    Valid characters: C, F, G, H, J, K, L, M, N, P, R, T, V, W, X, Y, Z, 0-9
    Excluded: vowels (A, E, I, O, U) and confusable letters (B, D, Q, S)

    Checksum: weighted sum with weights 7, 3, 1 repeating.
    """

    entity_types = ["DE_PERSONAL_ID"]

    # Valid characters (no vowels, no confusable chars)
    VALID_CHARS = "CFGHJKLMNPRTVWXYZ0123456789"

    # Character values for checksum
    CHAR_VALUES = {
        "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
        "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "C": 12, "F": 15, "G": 16, "H": 17, "J": 19,
        "K": 20, "L": 21, "M": 22, "N": 23, "P": 25,
        "R": 27, "T": 29, "V": 31, "W": 32, "X": 33,
        "Y": 34, "Z": 35,
    }

    def generate(self, **kwargs) -> Entity:
        """Generate a valid German Personal ID."""
        # Generate 9 characters (8 random + 1 check digit)
        chars = [random.choice(self.VALID_CHARS) for _ in range(8)]

        # Calculate check digit
        check_digit = self._calculate_checksum(chars)
        chars.append(str(check_digit))

        personal_id = ''.join(chars)

        return Entity(
            entity_type="DE_PERSONAL_ID",
            value=personal_id,
            variants=[
                personal_id,
                f"Ausweis-Nr.: {personal_id}",
                f"Personalausweis {personal_id}",
            ],
            metadata={},
        )

    def _calculate_checksum(self, chars: List[str]) -> int:
        """Calculate check digit using weighted sum (7, 3, 1)."""
        weights = [7, 3, 1]
        total = 0

        for i, char in enumerate(chars):
            value = self.CHAR_VALUES.get(char, 0)
            total += value * weights[i % 3]

        return total % 10


class SocialSecurityGenerator(BaseGenerator):
    """Generate valid German Social Security Number (Sozialversicherungsnummer).

    Format: 12 characters - BBTTMMJJASSP
    - BB: Area code (Bereichsnummer) - 2 digits
    - TTMMJJ: Birth date (day, month, year) - 6 digits
    - A: First letter of birth surname - 1 letter
    - SS: Serial number - 2 digits
    - P: Check digit - 1 digit

    Checksum: VKVV § 2 with weights [2,1,2,5,7,1,2,1,2,1,2,1]
    """

    entity_types = ["DE_SOCIAL_SECURITY"]

    VALID_AREA_CODES = [
        "02", "03", "04", "05", "06", "07", "08", "09",
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
        "38", "39", "40", "42", "43", "44", "45", "46", "47", "48", "49",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
        "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
    ]

    CHECKSUM_WEIGHTS = [2, 1, 2, 5, 7, 1, 2, 1, 2, 1, 2, 1]

    def generate(self, **kwargs) -> Entity:
        """Generate a valid German Social Security Number."""
        # Area code
        area_code = random.choice(self.VALID_AREA_CODES)

        # Birth date (valid date)
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(40, 99)  # 1940-1999

        # First letter of surname
        letter = random.choice(string.ascii_uppercase)

        # Serial number
        serial = f"{random.randint(0, 99):02d}"

        # Build base number (without check digit)
        base = f"{area_code}{day:02d}{month:02d}{year:02d}{letter}{serial}"

        # Calculate check digit
        check_digit = self._calculate_checksum(base)

        svnr = base + str(check_digit)

        return Entity(
            entity_type="DE_SOCIAL_SECURITY",
            value=svnr,
            variants=[
                svnr,
                f"{svnr[:2]} {svnr[2:8]} {svnr[8]} {svnr[9:]}",
                f"SVNR: {svnr}",
                f"Rentenversicherungsnummer {svnr}",
            ],
            metadata={
                "area_code": area_code,
                "birth_day": day,
                "birth_month": month,
                "birth_year": 1900 + year,
                "surname_initial": letter,
            },
        )

    def _calculate_checksum(self, base: str) -> int:
        """Calculate check digit per VKVV § 2."""
        # Convert letter (position 8, 0-indexed) to 2-digit number
        letter = base[8]
        letter_value = ord(letter) - ord('A') + 1

        # Build 12-digit string: BBTTMMJJ + letter(2 digits) + SS
        number_str = base[:8] + f"{letter_value:02d}" + base[9:11]

        # Apply weights and sum digit sums (Quersummen)
        total = 0
        for i, char in enumerate(number_str):
            digit = int(char)
            product = digit * self.CHECKSUM_WEIGHTS[i]
            # Add digit sum of product
            total += product // 10 + product % 10

        return total % 10


class PassportGenerator(BaseGenerator):
    """Generate valid German Passport Number (Reisepassnummer).

    Format: 9 alphanumeric characters.
    - First character: C, F, G, H, J, or K
    - Remaining: valid characters (no vowels, no confusable)
    - Last character: check digit

    Checksum: weighted sum with weights 7, 3, 1 repeating.
    """

    entity_types = ["DE_PASSPORT"]

    VALID_PREFIXES = ["C", "F", "G", "H", "J", "K"]
    VALID_CHARS = "CFGHJKLMNPRTVWXYZ0123456789"

    CHAR_VALUES = {
        "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
        "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "C": 12, "F": 15, "G": 16, "H": 17, "J": 19,
        "K": 20, "L": 21, "M": 22, "N": 23, "P": 25,
        "R": 27, "T": 29, "V": 31, "W": 32, "X": 33,
        "Y": 34, "Z": 35,
    }

    def generate(self, **kwargs) -> Entity:
        """Generate a valid German Passport Number."""
        # First character is a valid prefix
        chars = [random.choice(self.VALID_PREFIXES)]

        # Generate 7 more random valid characters
        chars.extend([random.choice(self.VALID_CHARS) for _ in range(7)])

        # Calculate check digit
        check_digit = self._calculate_checksum(chars)
        chars.append(str(check_digit))

        passport = ''.join(chars)

        return Entity(
            entity_type="DE_PASSPORT",
            value=passport,
            variants=[
                passport,
                f"Reisepass-Nr.: {passport}",
                f"Pass {passport}",
            ],
            metadata={},
        )

    def _calculate_checksum(self, chars: List[str]) -> int:
        """Calculate check digit using weighted sum (7, 3, 1)."""
        weights = [7, 3, 1]
        total = 0

        for i, char in enumerate(chars):
            value = self.CHAR_VALUES.get(char, 0)
            total += value * weights[i % 3]

        return total % 10


class DriverLicenseGenerator(BaseGenerator):
    """Generate German Driver's License Number (Führerscheinnummer).

    Format varies by issuing authority. EU card format since 2013:
    - Typically 11 alphanumeric characters
    - No standardized checksum across all formats
    """

    entity_types = ["DE_DRIVER_LICENSE"]

    def generate(self, **kwargs) -> Entity:
        """Generate a German Driver's License Number."""
        # Format: X00XXXXXXXX (letter + 2 digits + 8 alphanumeric)
        first_letter = random.choice(string.ascii_uppercase)
        digits = f"{random.randint(0, 99):02d}"
        rest = ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )

        license_num = first_letter + digits + rest

        return Entity(
            entity_type="DE_DRIVER_LICENSE",
            value=license_num,
            variants=[
                license_num,
                f"Führerschein-Nr.: {license_num}",
                f"FS-Nr. {license_num}",
            ],
            metadata={},
        )


class LicensePlateGenerator(BaseGenerator):
    """Generate German License Plate (KFZ-Kennzeichen).

    Format: [District 1-3 letters]-[Recognition 1-2 letters] [1-4 digits][E/H]

    Examples:
    - B-AB 1234 (Berlin)
    - M-XY 123E (Munich, electric)
    - HH-OL 99H (Hamburg, historic)

    Length constraint: 5-8 characters (excluding separators).
    """

    entity_types = ["DE_LICENSE_PLATE"]

    # Common district codes
    DISTRICT_CODES = [
        "B", "HH", "M", "K", "F", "S", "D", "L", "DD", "HB",
        "N", "H", "DO", "E", "DU", "BO", "W", "MH", "GE", "AC",
        "A", "KA", "MA", "WI", "MS", "KS", "KI", "LU", "OB", "HA",
        "MG", "KR", "BN", "OS", "SG", "PB", "OL", "RE", "WU", "TÜ",
    ]

    def generate(self, **kwargs) -> Entity:
        """Generate a German License Plate."""
        # Keep generating until we get a valid length (5-8 chars)
        while True:
            district = random.choice(self.DISTRICT_CODES)

            # Recognition letters (1-2)
            num_recognition = random.choice([1, 2])
            recognition = ''.join(
                random.choice(string.ascii_uppercase)
                for _ in range(num_recognition)
            )

            # Digits (1-4, not starting with 0)
            num_digits = random.randint(1, 4)
            if num_digits == 1:
                digits = str(random.randint(1, 9))
            else:
                digits = str(random.randint(1, 9)) + ''.join(
                    str(random.randint(0, 9)) for _ in range(num_digits - 1)
                )

            # Optional suffix (E for electric, H for historic)
            suffix = random.choices(["", "E", "H"], weights=[0.85, 0.10, 0.05])[0]

            # Check total length (excluding separators): 5-8 chars
            total_len = len(district) + len(recognition) + len(digits) + len(suffix)
            if 5 <= total_len <= 8:
                break

        # Format with hyphen and space
        plate = f"{district}-{recognition} {digits}{suffix}"

        return Entity(
            entity_type="DE_LICENSE_PLATE",
            value=plate,
            variants=[
                plate,
                f"{district} {recognition} {digits}{suffix}",
                f"{district}{recognition}{digits}{suffix}",
                f"Kennzeichen: {plate}",
            ],
            metadata={
                "district": district,
                "recognition": recognition,
                "digits": digits,
                "suffix": suffix if suffix else None,
            },
        )
