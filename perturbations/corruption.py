"""Grammar and spelling corruption perturbations.

Simulates common errors in real-world German text:
- Dropped articles
- Wrong article gender
- Missing umlauts
- Case errors
"""

import random
from typing import List, Tuple

from synpii.perturbations.base import BasePerturbation


class GrammarCorruption(BasePerturbation):
    """Apply grammatical errors common in real German text.

    Types of corruption:
    - Article dropping: "an der Brücke" → "an Brücke"
    - Wrong article: "an der Brücke" → "an dem Brücke"
    - Case corruption: preserved but grammatically incorrect
    """

    default_probability = 0.2

    # Articles that can be dropped
    DROPPABLE_ARTICLES = ["der", "die", "das", "dem", "den", "des", "ein", "eine", "einem", "einen", "einer"]

    # Article substitution pairs (incorrect usage)
    ARTICLE_CONFUSIONS = [
        ("der", "die"), ("die", "der"),
        ("dem", "der"), ("der", "dem"),
        ("den", "dem"), ("dem", "den"),
        ("das", "die"), ("die", "das"),
        ("einem", "einer"), ("einer", "einem"),
    ]

    def __init__(
        self,
        probability: float = None,
        corruption_types: List[str] = None,
        seed: int = None,
    ):
        """Initialize grammar corruption.

        Args:
            probability: Chance of applying perturbation.
            corruption_types: List of corruption types to apply.
                Options: 'drop_article', 'wrong_article', 'all'
            seed: Random seed.
        """
        super().__init__(probability, seed)
        self.corruption_types = corruption_types or ['drop_article', 'wrong_article']

    def apply(self, text: str) -> str:
        """Apply grammar corruption to text.

        Args:
            text: Input text.

        Returns:
            Text with grammatical errors.
        """
        corruption_type = random.choice(self.corruption_types)

        if corruption_type == 'drop_article':
            return self._drop_article(text)
        elif corruption_type == 'wrong_article':
            return self._wrong_article(text)
        else:
            # Randomly choose
            if random.random() < 0.5:
                return self._drop_article(text)
            else:
                return self._wrong_article(text)

    def _drop_article(self, text: str) -> str:
        """Remove an article from text."""
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in self.DROPPABLE_ARTICLES:
                # Drop this article
                return ' '.join(words[:i] + words[i + 1:])
        return text  # No article found

    def _wrong_article(self, text: str) -> str:
        """Replace an article with incorrect one."""
        for original, replacement in self.ARTICLE_CONFUSIONS:
            # Check for word boundary (not part of larger word)
            if f" {original} " in f" {text} ":
                # Preserve capitalization
                if text.startswith(original.capitalize()):
                    return text.replace(original.capitalize(), replacement.capitalize(), 1)
                return text.replace(f" {original} ", f" {replacement} ", 1)
        return text


class UmlautCorruption(BasePerturbation):
    """Corrupt or remove umlauts.

    Simulates:
    - Missing umlauts (common in ASCII-only systems)
    - Incorrect umlaut usage
    """

    default_probability = 0.15

    def apply(self, text: str) -> str:
        """Remove or corrupt umlauts.

        Args:
            text: Input text.

        Returns:
            Text with corrupted umlauts.
        """
        result = text

        # Remove umlauts (most common error)
        umlaut_map = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U'}

        for umlaut, base in umlaut_map.items():
            if umlaut in result:
                result = result.replace(umlaut, base, 1)  # Only first occurrence
                break

        return result


class CaseCorruption(BasePerturbation):
    """Corrupt letter case.

    Simulates:
    - Lowercase where uppercase expected (German nouns)
    - All-caps input
    - Random case errors
    """

    default_probability = 0.1

    def __init__(
        self,
        probability: float = None,
        corruption_style: str = "lowercase_noun",
        seed: int = None,
    ):
        """Initialize case corruption.

        Args:
            probability: Chance of applying perturbation.
            corruption_style: 'lowercase_noun', 'all_caps', 'random'
            seed: Random seed.
        """
        super().__init__(probability, seed)
        self.corruption_style = corruption_style

    def apply(self, text: str) -> str:
        """Corrupt case in text.

        Args:
            text: Input text.

        Returns:
            Text with case errors.
        """
        if self.corruption_style == "all_caps":
            return text.upper()
        elif self.corruption_style == "lowercase_noun":
            # Lowercase the first letter if it's uppercase (common German noun error)
            if text and text[0].isupper():
                return text[0].lower() + text[1:]
            return text
        else:  # random
            # Flip case of one random letter
            letters = [(i, c) for i, c in enumerate(text) if c.isalpha()]
            if letters:
                idx, char = random.choice(letters)
                flipped = char.lower() if char.isupper() else char.upper()
                return text[:idx] + flipped + text[idx + 1:]
            return text


class SpacingCorruption(BasePerturbation):
    """Corrupt spacing in text.

    Simulates:
    - Missing spaces (common in OCR)
    - Extra spaces
    - Space replaced with other whitespace
    """

    default_probability = 0.1

    def apply(self, text: str) -> str:
        """Corrupt spacing in text.

        Args:
            text: Input text.

        Returns:
            Text with spacing errors.
        """
        corruption = random.choice(['remove', 'add', 'double'])

        if corruption == 'remove' and ' ' in text:
            # Remove one space
            space_positions = [i for i, c in enumerate(text) if c == ' ']
            if space_positions:
                pos = random.choice(space_positions)
                return text[:pos] + text[pos + 1:]

        elif corruption == 'add':
            # Add extra space at random position
            if len(text) > 2:
                pos = random.randint(1, len(text) - 1)
                return text[:pos] + ' ' + text[pos:]

        elif corruption == 'double' and ' ' in text:
            # Double a space
            return text.replace(' ', '  ', 1)

        return text
