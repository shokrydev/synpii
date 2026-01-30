"""Weakness-targeted generator for detection system analysis.

Provides the main API for generating test cases that target
specific detection weaknesses.
"""

from typing import Dict, List, Type, Optional

from synpii.weakness.types import WeaknessType, WeaknessReport, WeaknessTestCase
from synpii.weakness.strategies import (
    BaseWeaknessStrategy,
    OverlapConflictStrategy,
    FormatVariationStrategy,
    ContextDependencyStrategy,
    CoverageGapStrategy,
    EntityConfusionStrategy,
)
from synpii.generators.base import GeneratorRegistry
from synpii.core.lexicon import GermanLexicon


class WeaknessTargetedGenerator:
    """Generate test cases targeting specific detection weaknesses.

    Integration point for the piigent Weakness Analyzer agent.

    Example:
        from synpii import SynPII
        from synpii.weakness import WeaknessTargetedGenerator, WeaknessReport, WeaknessType

        synpii = SynPII(preset="benchmark_adversarial")
        generator = WeaknessTargetedGenerator(
            generators=synpii.generators,
            lexicon=synpii.lexicon,
        )

        # Generate test cases for a specific weakness
        weakness = WeaknessReport(
            weakness_type=WeaknessType.OVERLAP_CONFLICT,
            entity_type="DE_POSTAL_CODE",
            description="PLZ overlaps with LOCATION",
            evidence={"conflicting_type": "LOCATION"},
        )

        test_cases = generator.generate_for_weakness(weakness, count=50)
    """

    # Map weakness types to strategies
    STRATEGIES: Dict[WeaknessType, Type[BaseWeaknessStrategy]] = {
        WeaknessType.OVERLAP_CONFLICT: OverlapConflictStrategy,
        WeaknessType.FORMAT_VARIATION: FormatVariationStrategy,
        WeaknessType.CONTEXT_DEPENDENCY: ContextDependencyStrategy,
        WeaknessType.COVERAGE_GAP: CoverageGapStrategy,
        WeaknessType.ENTITY_CONFUSION: EntityConfusionStrategy,
    }

    def __init__(
        self,
        generators: GeneratorRegistry = None,
        lexicon: GermanLexicon = None,
    ):
        """Initialize weakness-targeted generator.

        Args:
            generators: Entity generator registry.
            lexicon: German lexicon for values.
        """
        self.generators = generators
        self.lexicon = lexicon

        # Initialize strategy instances
        self._strategies: Dict[WeaknessType, BaseWeaknessStrategy] = {}
        for weakness_type, strategy_cls in self.STRATEGIES.items():
            self._strategies[weakness_type] = strategy_cls(
                generators=generators,
                lexicon=lexicon,
            )

    def generate_for_weakness(
        self,
        weakness: WeaknessReport,
        count: int = 10,
    ) -> List[WeaknessTestCase]:
        """Generate test cases for a specific weakness.

        Args:
            weakness: WeaknessReport describing the weakness to target.
            count: Number of test cases to generate.

        Returns:
            List of WeaknessTestCase objects.
        """
        strategy = self._strategies.get(weakness.weakness_type)
        if strategy is None:
            raise ValueError(
                f"No strategy for weakness type: {weakness.weakness_type}. "
                f"Available: {list(self._strategies.keys())}"
            )

        return strategy.generate(weakness, count)

    def generate_for_type(
        self,
        weakness_type: WeaknessType,
        entity_type: str,
        count: int = 10,
        **evidence,
    ) -> List[WeaknessTestCase]:
        """Convenience method to generate without creating a WeaknessReport.

        Args:
            weakness_type: Type of weakness to target.
            entity_type: Primary entity type affected.
            count: Number of test cases.
            **evidence: Additional evidence for the weakness.

        Returns:
            List of WeaknessTestCase objects.
        """
        weakness = WeaknessReport(
            weakness_type=weakness_type,
            entity_type=entity_type,
            description=f"Test {weakness_type.value} for {entity_type}",
            evidence=evidence,
        )
        return self.generate_for_weakness(weakness, count)

    def generate_exploration_batch(
        self,
        entity_types: List[str] = None,
        count_per_type: int = 5,
    ) -> Dict[str, List[WeaknessTestCase]]:
        """Generate a batch of test cases for exploration.

        Useful for initial weakness discovery - generates test cases
        for all weakness types and entity types.

        Args:
            entity_types: Entity types to test (default: common German types).
            count_per_type: Cases per entity type per weakness type.

        Returns:
            Dict mapping weakness type names to test case lists.
        """
        if entity_types is None:
            entity_types = [
                "PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER",
                "DE_KVNR", "DE_POSTAL_CODE", "ORGANIZATION",
            ]

        results: Dict[str, List[WeaknessTestCase]] = {}

        for weakness_type in self.STRATEGIES.keys():
            cases = []
            for entity_type in entity_types:
                try:
                    cases.extend(self.generate_for_type(
                        weakness_type=weakness_type,
                        entity_type=entity_type,
                        count=count_per_type,
                    ))
                except Exception:
                    # Skip unsupported combinations
                    continue

            results[weakness_type.value] = cases

        return results

    @property
    def available_weakness_types(self) -> List[WeaknessType]:
        """Get list of supported weakness types."""
        return list(self._strategies.keys())

    def register_strategy(
        self,
        weakness_type: WeaknessType,
        strategy_cls: Type[BaseWeaknessStrategy],
    ) -> None:
        """Register a custom strategy for a weakness type.

        Args:
            weakness_type: The weakness type to handle.
            strategy_cls: Strategy class to use.
        """
        self._strategies[weakness_type] = strategy_cls(
            generators=self.generators,
            lexicon=self.lexicon,
        )
