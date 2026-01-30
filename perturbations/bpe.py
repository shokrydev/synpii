"""BPE (Byte Pair Encoding) perturbation.

Simulates artifacts from tokenization that can confuse detection:
- Mid-word hyphenation
- Subword splits that break entity patterns
"""

import random
from typing import List, Tuple

from synpii.perturbations.base import BasePerturbation


class BPEPerturbation(BasePerturbation):
    """Apply BPE-like tokenization artifacts.

    These artifacts commonly occur in:
    - Scanned documents with line breaks
    - Copy-paste from PDFs
    - Text preprocessed by language models

    Examples:
    - "Goethestraße" → "Goethe-straße"
    - "Krankenversichertennummer" → "Kranken-versicherten-nummer"
    """

    default_probability = 0.2

    # Common break points in German compound words
    BREAK_PATTERNS: List[Tuple[str, str]] = [
        ("straße", "-straße"),
        ("weg", "-weg"),
        ("platz", "-platz"),
        ("gasse", "-gasse"),
        ("allee", "-allee"),
        ("krankenhaus", "-krankenhaus"),
        ("klinikum", "-klinikum"),
        ("praxis", "-praxis"),
        ("versicherten", "-versicherten"),
        ("nummer", "-nummer"),
    ]

    def __init__(
        self,
        probability: float = None,
        seed: int = None,
    ):
        """Initialize BPE perturbation.

        Args:
            probability: Chance of applying perturbation.
            seed: Random seed.
        """
        super().__init__(probability, seed)

    def apply(self, text: str) -> str:
        """Apply BPE-like word breaks.

        Args:
            text: Input text.

        Returns:
            Text with artificial word breaks.
        """
        result = text

        # Try to apply one break pattern
        for original, replacement in self.BREAK_PATTERNS:
            if original.lower() in result.lower():
                # Find and replace (case-insensitive position, preserve case)
                lower_result = result.lower()
                pos = lower_result.find(original.lower())
                if pos > 0:  # Don't break at start of word
                    # Check if there's a letter before (word-internal)
                    if result[pos - 1].isalpha():
                        # Preserve original case of replacement
                        if result[pos].isupper():
                            actual_replacement = replacement[0] + replacement[1].upper() + replacement[2:]
                        else:
                            actual_replacement = replacement
                        result = result[:pos] + actual_replacement + result[pos + len(original):]
                        break  # Only one break per text

        return result

    def can_apply(self, text: str) -> bool:
        """Check if BPE breaks can be applied."""
        text_lower = text.lower()
        return any(pattern[0].lower() in text_lower for pattern in self.BREAK_PATTERNS)


class MidWordHyphenation(BasePerturbation):
    """Insert mid-word hyphens at arbitrary positions.

    Simulates line breaks in narrow column layouts or
    poor PDF text extraction.
    """

    default_probability = 0.15

    def __init__(
        self,
        probability: float = None,
        min_word_length: int = 8,
        seed: int = None,
    ):
        """Initialize mid-word hyphenation.

        Args:
            probability: Chance of applying perturbation.
            min_word_length: Minimum word length to hyphenate.
            seed: Random seed.
        """
        super().__init__(probability, seed)
        self.min_word_length = min_word_length

    def apply(self, text: str) -> str:
        """Insert a hyphen at a random position in long words.

        Args:
            text: Input text.

        Returns:
            Text with inserted hyphen.
        """
        if len(text) < self.min_word_length:
            return text

        # Find a good break position (between letters, not at start/end)
        valid_positions = []
        for i in range(2, len(text) - 2):
            if text[i - 1].isalpha() and text[i].isalpha():
                # Prefer positions between consonant and vowel
                if self._is_consonant(text[i - 1]) and self._is_vowel(text[i]):
                    valid_positions.append((i, 2))  # Higher weight
                elif self._is_vowel(text[i - 1]) and self._is_consonant(text[i]):
                    valid_positions.append((i, 1))

        if not valid_positions:
            return text

        # Weight-based selection
        total_weight = sum(w for _, w in valid_positions)
        r = random.random() * total_weight
        cumulative = 0
        for pos, weight in valid_positions:
            cumulative += weight
            if r <= cumulative:
                return text[:pos] + "-" + text[pos:]

        return text

    def _is_vowel(self, char: str) -> bool:
        return char.lower() in "aeiouäöü"

    def _is_consonant(self, char: str) -> bool:
        return char.isalpha() and not self._is_vowel(char)
