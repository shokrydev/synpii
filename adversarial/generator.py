"""Main generator for adversarial scenarios.

Orchestrates adversarial recipes to produce targeted test samples that
challenge PII detection systems.
"""

from typing import Dict, List, Optional, Type

from synpii.adversarial.types import (
    AdversarialType,
    AdversarialScenario,
    AdversarialSample,
)
from synpii.adversarial.scenarios import (
    AdversarialRecipe,
    OverlapScenario,
    FormatScenario,
    ContextScenario,
    CoverageScenario,
    ConfusionScenario,
)
from synpii.generators.base import GeneratorRegistry
from synpii.core.lexicon import GermanLexicon
from synpii.templates.engine import TemplateEngine


class AdversarialGenerator:
    """Orchestrator for targeted adversarial scenario generation.

    Maps AdversarialType to specific generative recipes (scenarios).
    """

    # Registration of available recipes
    RECIPES: Dict[AdversarialType, Type[AdversarialRecipe]] = {
        AdversarialType.OVERLAP_CONFLICT: OverlapScenario,
        AdversarialType.FORMAT_VARIATION: FormatScenario,
        AdversarialType.CONTEXT_DEPENDENCY: ContextScenario,
        AdversarialType.COVERAGE_GAP: CoverageScenario,
        AdversarialType.ENTITY_CONFUSION: ConfusionScenario,
    }

    def __init__(
        self,
        generators: GeneratorRegistry = None,
        lexicon: GermanLexicon = None,
        template_engine: TemplateEngine = None,
    ):
        """Initialize adversarial generator.

        Args:
            generators: Entity generator registry.
            lexicon: German lexicon.
            template_engine: Shared template engine.
        """
        self.generators = generators
        self.lexicon = lexicon
        self.template_engine = template_engine or TemplateEngine(lexicon=lexicon)
        self._recipes: Dict[AdversarialType, AdversarialRecipe] = {}

        # Initialize all registered recipes
        for adv_type, recipe_cls in self.RECIPES.items():
            self._recipes[adv_type] = recipe_cls(
                generators=generators,
                lexicon=lexicon,
                template_engine=self.template_engine,
            )

    def generate_for_scenario(
        self,
        scenario: AdversarialScenario,
        count: int = 10,
    ) -> List[AdversarialSample]:
        """Generate adversarial samples for a specific research scenario.

        Args:
            scenario: The targeted scenario description.
            count: Number of samples to generate.

        Returns:
            List of AdversarialSample objects.
        """
        recipe = self._recipes.get(scenario.adversarial_type)
        if not recipe:
            return []

        return recipe.generate(scenario, count=count)

    def register_recipe(self, adv_type: AdversarialType, recipe_cls: Type[AdversarialRecipe]):
        """Register a new generative recipe.

        Allows extending the generator with custom adversarial logic.
        """
        self._recipes[adv_type] = recipe_cls(
            generators=self.generators,
            lexicon=self.lexicon,
            template_engine=self.template_engine,
        )
