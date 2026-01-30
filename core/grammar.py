"""PCFG (Probabilistic Context-Free Grammar) engine for generating text.

Supports weighted productions for realistic frequency distributions.
"""

import random
from typing import Dict, List, Tuple, Union, Callable, Any


class PCFGEngine:
    """Probabilistic Context-Free Grammar engine.

    Supports:
    - Weighted productions with Zipfian-like distributions
    - Terminal callbacks for dynamic value generation
    - Optional symbols (marked with ?)
    - Recursive expansion with depth limits

    Example:
        grammar = {
            "STREET": [
                (["STREET_BASE"], 0.60),
                (["STREET_PREP"], 0.25),
                (["STREET_DATE"], 0.15),
            ],
            "STREET_BASE": [
                (["NAME", "SUFFIX"], 0.75),
                (["NAME", "NAME", "SUFFIX"], 0.25),
            ],
        }

        terminals = {
            "NAME": lambda: random.choice(["Goethe", "Schiller", "Bach"]),
            "SUFFIX": lambda: random.choice(["straße", "weg", "platz"]),
        }

        engine = PCFGEngine(grammar, terminals)
        street = engine.expand("STREET")  # e.g., "Goethestraße"
    """

    def __init__(
        self,
        grammar: Dict[str, List[Tuple[List[str], float]]],
        terminals: Dict[str, Union[str, List[str], Callable[[], str]]] = None,
        max_depth: int = 10,
    ):
        """Initialize PCFG engine.

        Args:
            grammar: Dict mapping non-terminals to list of (production, weight) tuples.
            terminals: Dict mapping terminal symbols to values or generators.
            max_depth: Maximum recursion depth for expansion.
        """
        self.grammar = grammar
        self.terminals = terminals or {}
        self.max_depth = max_depth

        # Normalize weights for each non-terminal
        self._normalized_grammar = self._normalize_weights(grammar)

    def _normalize_weights(
        self, grammar: Dict[str, List[Tuple[List[str], float]]]
    ) -> Dict[str, List[Tuple[List[str], float]]]:
        """Normalize production weights to sum to 1.0."""
        normalized = {}
        for symbol, productions in grammar.items():
            total_weight = sum(weight for _, weight in productions)
            if total_weight == 0:
                # Equal probability if all weights are 0
                n = len(productions)
                normalized[symbol] = [(prod, 1.0 / n) for prod, _ in productions]
            else:
                normalized[symbol] = [
                    (prod, weight / total_weight) for prod, weight in productions
                ]
        return normalized

    def _select_production(
        self, productions: List[Tuple[List[str], float]]
    ) -> List[str]:
        """Select a production based on weights."""
        r = random.random()
        cumulative = 0.0
        for production, weight in productions:
            cumulative += weight
            if r <= cumulative:
                return production
        # Fallback to last production (handles floating point edge cases)
        return productions[-1][0]

    def _resolve_terminal(self, symbol: str) -> str:
        """Resolve a terminal symbol to its value."""
        if symbol not in self.terminals:
            return symbol  # Literal terminal

        value = self.terminals[symbol]

        if callable(value):
            return value()
        elif isinstance(value, list):
            return random.choice(value)
        else:
            return str(value)

    def expand(self, symbol: str, depth: int = 0) -> str:
        """Expand a symbol according to the grammar.

        Args:
            symbol: The symbol to expand.
            depth: Current recursion depth.

        Returns:
            Expanded string.
        """
        if depth >= self.max_depth:
            # At max depth, try to resolve as terminal
            return self._resolve_terminal(symbol)

        # Handle optional symbols (ends with ?)
        if symbol.endswith("?"):
            base_symbol = symbol[:-1]
            # 50% chance to include optional symbol
            if random.random() < 0.5:
                return ""
            symbol = base_symbol

        # Check if it's a non-terminal
        if symbol in self._normalized_grammar:
            production = self._select_production(self._normalized_grammar[symbol])
            # Expand each symbol in the production
            parts = []
            for sub_symbol in production:
                expanded = self.expand(sub_symbol, depth + 1)
                if expanded:  # Skip empty strings from optional symbols
                    parts.append(expanded)
            # Join without spaces for compound words, with spaces for phrases
            if self._is_compound_production(production):
                return "".join(parts)
            return " ".join(parts) if parts else ""

        # It's a terminal
        return self._resolve_terminal(symbol)

    def _is_compound_production(self, production: List[str]) -> bool:
        """Check if production should be joined without spaces (compound words)."""
        # Heuristic: if it's a name + suffix pattern, join without spaces
        compound_patterns = [
            ["NAME", "SUFFIX"],
            ["NAME", "s", "SUFFIX"],
            ["NAME", "ens", "SUFFIX"],
            ["LOCATION_NOUN", "SUFFIX"],
        ]
        return production in compound_patterns

    def add_production(
        self, symbol: str, production: List[str], weight: float = 1.0
    ) -> None:
        """Add a new production to the grammar.

        Args:
            symbol: The non-terminal symbol.
            production: List of symbols in the production.
            weight: Production weight.
        """
        if symbol not in self.grammar:
            self.grammar[symbol] = []
        self.grammar[symbol].append((production, weight))
        self._normalized_grammar = self._normalize_weights(self.grammar)

    def set_terminal(
        self, symbol: str, value: Union[str, List[str], Callable[[], str]]
    ) -> None:
        """Set or update a terminal symbol.

        Args:
            symbol: The terminal symbol.
            value: Value, list of values, or generator function.
        """
        self.terminals[symbol] = value


# Pre-defined German street grammar
GERMAN_STREET_GRAMMAR = {
    "STREET": [
        (["STREET_BASE"], 0.30),           # Goethestraße
        (["STREET_COMPOUND"], 0.20),       # Karl-Marx-Straße
        (["STREET_GENITIVE"], 0.08),       # Goethes Weg
        (["STREET_PREP"], 0.15),           # Am Markt, An der Brücke
        (["STREET_DATE"], 0.05),           # Straße des 17. Juni
        (["STREET_NUMERIC"], 0.06),        # 1. Straße
        (["STREET_ABBREV"], 0.08),         # Goethe Str.
        (["STREET_SPECIAL"], 0.08),        # Alte/Neue/Kleine/Große ...
    ],
    "STREET_BASE": [
        (["NAME", "SUFFIX"], 0.70),
        (["NAME", "NAME", "SUFFIX"], 0.15),
        (["LOCATION_NOUN", "SUFFIX"], 0.15),
    ],
    "STREET_COMPOUND": [
        (["NAME", "-", "NAME", "-", "SUFFIX"], 0.60),
        (["NAME", "-", "NAME", "-", "NAME", "-", "SUFFIX"], 0.20),
        (["NAME", "-", "und", "-", "NAME", "-", "SUFFIX"], 0.20),
    ],
    "STREET_GENITIVE": [
        (["NAME", "s", "SUFFIX"], 0.70),
        (["NAME", "ens", "SUFFIX"], 0.30),
    ],
    "STREET_PREP": [
        (["PREP_PHRASE", "LOCATION_NOUN"], 0.50),
        (["PREP_PHRASE", "ADJ?", "LOCATION_NOUN"], 0.30),
        (["SIMPLE_PREP", "LOCATION_NOUN"], 0.20),
    ],
    "STREET_DATE": [
        (["SUFFIX", "des", "ORDINAL", ".", "MONTH"], 0.50),
        (["SUFFIX", "des", "DAY", ".", "MONTH", "YEAR"], 0.30),
        (["ORDINAL", ".", "MONTH", "-", "SUFFIX"], 0.20),
    ],
    "STREET_NUMERIC": [
        (["ORDINAL", ".", "SUFFIX"], 1.0),
    ],
    "STREET_ABBREV": [
        (["NAME", "Str."], 0.50),
        (["NAME", "str."], 0.30),
        (["NAME", "-Str."], 0.20),
    ],
    "STREET_SPECIAL": [
        (["SIZE_ADJ", "SUFFIX"], 0.40),
        (["AGE_ADJ", "SUFFIX"], 0.40),
        (["COLOR_ADJ", "SUFFIX"], 0.20),
    ],
}


def create_street_generator(lexicon: Any = None) -> PCFGEngine:
    """Create a PCFG engine for German street names.

    Args:
        lexicon: Optional GermanLexicon for terminal values.

    Returns:
        Configured PCFGEngine.
    """
    # Default terminals if no lexicon provided
    default_terminals = {
        "NAME": ["Goethe", "Schiller", "Bach", "Mozart", "Beethoven", "Kant", "Hegel",
                 "Luther", "Bismarck", "Adenauer", "Friedrich", "Wilhelm", "Karl", "Heinrich"],
        "SUFFIX": ["straße", "weg", "allee", "platz", "ring", "gasse", "damm", "ufer"],
        "LOCATION_NOUN": ["Markt", "Kirche", "Rathaus", "Brücke", "Wald", "Berg", "Wiese",
                         "Garten", "Hof", "Linde", "Eiche", "Rose"],
        "PREP_PHRASE": ["Am", "An der", "An den", "Auf der", "Auf dem", "Im", "In der",
                       "Unter den", "Zum", "Zur", "Bei der", "Beim"],
        "SIMPLE_PREP": ["Am", "Im", "Zum", "Zur", "Beim"],
        "ADJ": ["alten", "neuen", "kleinen", "großen", "schönen"],
        "SIZE_ADJ": ["Kleine", "Große", "Breite", "Lange", "Kurze"],
        "AGE_ADJ": ["Alte", "Neue"],
        "COLOR_ADJ": ["Grüne", "Weiße", "Rote", "Blaue"],
        "ORDINAL": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                    "11", "12", "13", "14", "15", "16", "17", "18"],
        "DAY": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
                "23", "24", "25", "26", "27", "28"],
        "MONTH": ["Januar", "Februar", "März", "April", "Mai", "Juni",
                  "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "YEAR": ["1848", "1871", "1918", "1945", "1953", "1989"],
    }

    terminals = default_terminals.copy()

    # Override with lexicon values if provided
    if lexicon is not None:
        if hasattr(lexicon, "street_names"):
            terminals["NAME"] = lambda: random.choice(lexicon.street_names)
        if hasattr(lexicon, "street_suffixes"):
            terminals["SUFFIX"] = lambda: random.choice(lexicon.street_suffixes)
        if hasattr(lexicon, "location_nouns"):
            terminals["LOCATION_NOUN"] = lambda: lexicon.sample_location_noun()

    return PCFGEngine(GERMAN_STREET_GRAMMAR, terminals)
