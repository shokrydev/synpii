"""OCR noise perturbation.

Simulates errors from optical character recognition (OCR) scanning
of documents, which commonly confuse visually similar characters.
"""

import random
from typing import List, Tuple

from synpii.perturbations.base import BasePerturbation


class OCRPerturbation(BasePerturbation):
    """Apply OCR-like character substitutions.

    Common OCR errors:
    - 0 ↔ O (zero vs letter O)
    - 1 ↔ I ↔ l (one vs I vs lowercase L)
    - rn ↔ m (letter combinations)
    - ß → ss (Eszett normalization)
    - Umlauts → base letters (ä→a, ö→o, ü→u)
    """

    default_probability = 0.3

    # Substitution rules: (original, replacement, probability)
    SUBSTITUTIONS: List[Tuple[str, str, float]] = [
        # Digit-letter confusions
        ("0", "O", 0.4),
        ("O", "0", 0.3),
        ("1", "I", 0.4),
        ("I", "1", 0.3),
        ("1", "l", 0.3),
        ("l", "1", 0.3),
        ("5", "S", 0.2),
        ("S", "5", 0.2),
        ("8", "B", 0.2),
        ("B", "8", 0.2),
        ("2", "Z", 0.15),
        ("Z", "2", 0.15),
        ("6", "G", 0.15),
        ("G", "6", 0.15),

        # Letter pair confusions
        ("rn", "m", 0.3),
        ("m", "rn", 0.2),
        ("cl", "d", 0.2),
        ("d", "cl", 0.15),
        ("vv", "w", 0.2),
        ("w", "vv", 0.15),

        # German-specific
        ("ß", "ss", 0.4),
        ("ß", "B", 0.1),
        ("ä", "a", 0.25),
        ("ö", "o", 0.25),
        ("ü", "u", 0.25),
        ("Ä", "A", 0.25),
        ("Ö", "O", 0.25),
        ("Ü", "U", 0.25),

        # Punctuation
        (".", ",", 0.1),
        (",", ".", 0.1),
        ("-", "_", 0.1),
        ("/", "1", 0.1),
    ]

    def __init__(
        self,
        probability: float = None,
        max_substitutions: int = 2,
        seed: int = None,
    ):
        """Initialize OCR perturbation.

        Args:
            probability: Chance of applying perturbation.
            max_substitutions: Maximum substitutions per text.
            seed: Random seed.
        """
        super().__init__(probability, seed)
        self.max_substitutions = max_substitutions

    def apply(self, text: str) -> str:
        """Apply OCR-like substitutions to text.

        Args:
            text: Input text.

        Returns:
            Text with OCR-like errors.
        """
        result = text
        applied = 0

        # Try each substitution rule
        for original, replacement, sub_prob in self.SUBSTITUTIONS:
            if applied >= self.max_substitutions:
                break

            if original in result and random.random() < sub_prob:
                # Replace one occurrence randomly
                positions = self._find_all(result, original)
                if positions:
                    pos = random.choice(positions)
                    result = result[:pos] + replacement + result[pos + len(original):]
                    applied += 1

        return result

    def _find_all(self, text: str, pattern: str) -> List[int]:
        """Find all occurrences of pattern in text."""
        positions = []
        start = 0
        while True:
            pos = text.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions


class UmlautNormalization(BasePerturbation):
    """Normalize German umlauts to ASCII equivalents.

    This is a common preprocessing step that can cause detection issues:
    - ä → ae
    - ö → oe
    - ü → ue
    - ß → ss
    """

    default_probability = 0.2

    NORMALIZATIONS = {
        "ä": "ae", "Ä": "Ae",
        "ö": "oe", "Ö": "Oe",
        "ü": "ue", "Ü": "Ue",
        "ß": "ss",
    }

    def apply(self, text: str) -> str:
        """Normalize umlauts to ASCII.

        Args:
            text: Input text with German umlauts.

        Returns:
            Text with ASCII-normalized umlauts.
        """
        result = text
        for original, replacement in self.NORMALIZATIONS.items():
            result = result.replace(original, replacement)
        return result
