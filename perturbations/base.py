"""Base perturbation interface."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import random


class BasePerturbation(ABC):
    """Abstract base class for text perturbations.

    Perturbations modify entity text to create adversarial examples
    that test detection robustness.

    Key principle: Apply perturbations to entity text ONLY, preserving
    span alignment by recomputing positions after modification.
    """

    # Probability of applying this perturbation (0.0-1.0)
    default_probability: float = 0.5

    def __init__(self, probability: float = None, seed: int = None):
        """Initialize perturbation.

        Args:
            probability: Chance of applying perturbation (0.0-1.0).
            seed: Random seed for reproducibility.
        """
        self.probability = probability if probability is not None else self.default_probability
        if seed is not None:
            random.seed(seed)

    @abstractmethod
    def apply(self, text: str) -> str:
        """Apply perturbation to text.

        Args:
            text: Input text (typically an entity value).

        Returns:
            Perturbed text.
        """
        pass

    def maybe_apply(self, text: str) -> Tuple[str, bool]:
        """Apply perturbation with probability check.

        Args:
            text: Input text.

        Returns:
            Tuple of (text, was_applied).
        """
        if random.random() < self.probability:
            return self.apply(text), True
        return text, False

    def can_apply(self, text: str) -> bool:
        """Check if this perturbation can be applied to the text.

        Override in subclasses for specific requirements.

        Args:
            text: Input text.

        Returns:
            True if perturbation can be applied.
        """
        return True

    @property
    def name(self) -> str:
        """Get perturbation name."""
        return self.__class__.__name__
