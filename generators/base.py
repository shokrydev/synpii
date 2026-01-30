"""Base generator interface and registry."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type

from synpii.core.types import Entity
from synpii.core.lexicon import GermanLexicon


class BaseGenerator(ABC):
    """Abstract base class for entity generators.

    All generators should inherit from this class and implement
    the generate() method.
    """

    # Entity type(s) this generator produces
    entity_types: List[str] = []

    def __init__(self, lexicon: Optional[GermanLexicon] = None, **kwargs):
        """Initialize generator.

        Args:
            lexicon: Optional GermanLexicon for value lookup.
            **kwargs: Additional configuration.
        """
        self.lexicon = lexicon
        self.config = kwargs

    @abstractmethod
    def generate(self, **kwargs) -> Entity:
        """Generate an entity.

        Args:
            **kwargs: Generation parameters.

        Returns:
            Generated Entity object.
        """
        pass

    def generate_batch(self, count: int, **kwargs) -> List[Entity]:
        """Generate multiple entities.

        Args:
            count: Number of entities to generate.
            **kwargs: Generation parameters passed to generate().

        Returns:
            List of Entity objects.
        """
        return [self.generate(**kwargs) for _ in range(count)]

    def get_variants(self, entity: Entity) -> List[str]:
        """Get all variant forms of an entity.

        Override in subclasses to provide additional variants.

        Args:
            entity: The entity to get variants for.

        Returns:
            List of variant strings.
        """
        return entity.variants


class GeneratorRegistry:
    """Registry of entity generators.

    Provides a unified interface to generate any entity type.

    Example:
        registry = GeneratorRegistry(lexicon)
        person = registry.generate("PERSON")
        kvnr = registry.generate("DE_KVNR")
    """

    def __init__(
        self,
        lexicon: Optional[GermanLexicon] = None,
        entity_types: Optional[List[str]] = None,
    ):
        """Initialize registry.

        Args:
            lexicon: GermanLexicon for value lookup.
            entity_types: Optional list of entity types to enable.
        """
        self.lexicon = lexicon
        self.enabled_types = set(entity_types) if entity_types else None
        self._generators: Dict[str, BaseGenerator] = {}
        self._register_default_generators()

    def _register_default_generators(self) -> None:
        """Register all default generators."""
        from synpii.generators.identifier import (
            KVNRGenerator,
            LANRGenerator,
            BSNRGenerator,
            TelematikIDGenerator,
            IBANGenerator,
            PostalCodeGenerator,
            TaxIDGenerator,
            PersonalIDGenerator,
            SocialSecurityGenerator,
            PassportGenerator,
            DriverLicenseGenerator,
            LicensePlateGenerator,
        )
        from synpii.generators.natural import (
            PersonGenerator,
            LocationGenerator,
            DateGenerator,
            PhoneGenerator,
            EmailGenerator,
            AgeGenerator,
        )
        from synpii.generators.clinical import OrganizationGenerator

        # Register each generator
        generators = [
            # Healthcare identifiers
            KVNRGenerator,
            LANRGenerator,
            BSNRGenerator,
            TelematikIDGenerator,
            # Financial identifiers
            IBANGenerator,
            PostalCodeGenerator,
            # Government identifiers
            TaxIDGenerator,
            PersonalIDGenerator,
            SocialSecurityGenerator,
            PassportGenerator,
            DriverLicenseGenerator,
            LicensePlateGenerator,
            # Natural language entities
            PersonGenerator,
            LocationGenerator,
            DateGenerator,
            PhoneGenerator,
            EmailGenerator,
            AgeGenerator,
            OrganizationGenerator,
        ]

        for generator_cls in generators:
            self.register(generator_cls)

    def register(self, generator_cls: Type[BaseGenerator], **kwargs) -> None:
        """Register a generator class.

        Args:
            generator_cls: Generator class to register.
            **kwargs: Additional arguments for generator instantiation.
        """
        instance = generator_cls(lexicon=self.lexicon, **kwargs)
        for entity_type in generator_cls.entity_types:
            # Only register if enabled (or all types enabled)
            if self.enabled_types is None or entity_type in self.enabled_types:
                self._generators[entity_type] = instance

    def generate(self, entity_type: str, **kwargs) -> Entity:
        """Generate an entity of the specified type.

        Args:
            entity_type: Type of entity to generate.
            **kwargs: Generation parameters.

        Returns:
            Generated Entity object.

        Raises:
            ValueError: If entity type not registered.
        """
        if entity_type not in self._generators:
            raise ValueError(
                f"Unknown entity type: {entity_type}. "
                f"Available: {list(self._generators.keys())}"
            )
        return self._generators[entity_type].generate(**kwargs)

    def generate_batch(
        self, entity_type: str, count: int, **kwargs
    ) -> List[Entity]:
        """Generate multiple entities of the specified type.

        Args:
            entity_type: Type of entity to generate.
            count: Number to generate.
            **kwargs: Generation parameters.

        Returns:
            List of Entity objects.
        """
        if entity_type not in self._generators:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return self._generators[entity_type].generate_batch(count, **kwargs)

    def get_generator(self, entity_type: str) -> Optional[BaseGenerator]:
        """Get the generator for an entity type.

        Args:
            entity_type: Entity type.

        Returns:
            Generator instance or None.
        """
        return self._generators.get(entity_type)

    @property
    def available_types(self) -> List[str]:
        """Get list of available entity types."""
        return list(self._generators.keys())

    def is_available(self, entity_type: str) -> bool:
        """Check if an entity type is available."""
        return entity_type in self._generators
