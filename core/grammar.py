"""PCFG (Probabilistic Context-Free Grammar) engine for generating text.

Supports weighted productions for realistic frequency distributions.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union, Callable, Any, Optional


@dataclass
class Token:
    """A token with join hints for proper German compound word formation."""
    text: str
    join_left: bool = False   # Join to previous token without space
    join_right: bool = False  # Next token joins to this without space
    capitalize: bool = False  # Capitalize when joining

    def __str__(self):
        return self.text


class PCFGEngine:
    """Probabilistic Context-Free Grammar engine.

    Supports:
    - Weighted productions with Zipfian-like distributions
    - Terminal callbacks for dynamic value generation
    - Optional symbols (marked with ?)
    - Structured token output for proper compound word handling
    """

    def __init__(
        self,
        grammar: Dict[str, List[Tuple[List[str], float]]],
        terminals: Dict[str, Union[str, List[str], Callable[[], str]]] = None,
        max_depth: int = 10,
    ):
        """Initialize PCFG engine."""
        self.grammar = grammar
        self.terminals = terminals or {}
        self.max_depth = max_depth
        self._normalized_grammar = self._normalize_weights(grammar)

    def _normalize_weights(
        self, grammar: Dict[str, List[Tuple[List[str], float]]]
    ) -> Dict[str, List[Tuple[List[str], float]]]:
        """Normalize production weights to sum to 1.0."""
        normalized = {}
        for symbol, productions in grammar.items():
            total_weight = sum(weight for _, weight in productions)
            if total_weight == 0:
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
        return productions[-1][0]

    def _resolve_terminal(self, symbol: str) -> str:
        """Resolve a terminal symbol to its value."""
        if symbol not in self.terminals:
            return symbol

        value = self.terminals[symbol]
        if callable(value):
            return value()
        elif isinstance(value, list):
            return random.choice(value)
        return str(value)

    def expand(self, symbol: str, depth: int = 0) -> str:
        """Expand a symbol and return properly formatted string."""
        tokens = self._expand_to_tokens(symbol, depth)
        return self._join_tokens(tokens)

    def _expand_to_tokens(self, symbol: str, depth: int = 0) -> List[Token]:
        """Expand a symbol to a list of tokens."""
        if depth >= self.max_depth:
            return [Token(self._resolve_terminal(symbol))]

        # Handle optional symbols
        if symbol.endswith("?"):
            if random.random() < 0.5:
                return []
            symbol = symbol[:-1]

        # Non-terminal expansion
        if symbol in self._normalized_grammar:
            production = self._select_production(self._normalized_grammar[symbol])
            tokens = []
            for sub_symbol in production:
                tokens.extend(self._expand_to_tokens(sub_symbol, depth + 1))
            return tokens

        # Terminal
        return [Token(self._resolve_terminal(symbol))]

    def _join_tokens(self, tokens: List[Token]) -> str:
        """Join tokens respecting join hints."""
        if not tokens:
            return ""

        result = []
        for i, token in enumerate(tokens):
            if not token.text:
                continue

            text = token.text
            if token.capitalize and result:
                text = text.capitalize()

            if i == 0:
                result.append(text)
            elif token.join_left or (result and tokens[i-1].join_right if i > 0 else False):
                result.append(text)
            else:
                result.append(" " + text)

        return "".join(result)

    def add_production(self, symbol: str, production: List[str], weight: float = 1.0):
        """Add a new production to the grammar."""
        if symbol not in self.grammar:
            self.grammar[symbol] = []
        self.grammar[symbol].append((production, weight))
        self._normalized_grammar = self._normalize_weights(self.grammar)

    def set_terminal(self, symbol: str, value: Union[str, List[str], Callable[[], str]]):
        """Set or update a terminal symbol."""
        self.terminals[symbol] = value


class GermanStreetGenerator:
    """Specialized generator for German street names.

    Handles proper compound word formation:
    - Goethestraße (name + suffix)
    - Karl-Marx-Straße (hyphenated compound)
    - Am Markt (prepositional)
    - Straße des 17. Juni (date memorial)
    """

    SUFFIXES = ["straße", "weg", "allee", "platz", "ring", "gasse", "damm", "ufer",
                "steig", "pfad", "hof", "markt", "brücke", "garten"]

    NAMES = ["Goethe", "Schiller", "Bach", "Mozart", "Beethoven", "Kant", "Hegel",
             "Luther", "Bismarck", "Adenauer", "Friedrich", "Wilhelm", "Karl",
             "Heinrich", "Rosa", "Luxemburg", "Leibniz", "Humboldt"]

    LOCATION_NOUNS = [
        ("Markt", "m"), ("Kirche", "f"), ("Rathaus", "n"), ("Brücke", "f"),
        ("Wald", "m"), ("Berg", "m"), ("Wiese", "f"), ("Garten", "m"),
        ("Hof", "m"), ("Linde", "f"), ("Eiche", "f"), ("Rose", "f"),
        ("Turm", "m"), ("Mühle", "f"), ("Brunnen", "m"),
    ]

    PREPS_DATIVE = {
        "m": [("Am", "am"), ("Beim", "beim"), ("Zum", "zum"), ("Im", "im")],
        "f": [("An der", "an der"), ("Bei der", "bei der"), ("Zur", "zur"), ("In der", "in der")],
        "n": [("Am", "am"), ("Beim", "beim"), ("Zum", "zum"), ("Im", "im")],
    }

    ADJECTIVES = ["Alte", "Neue", "Kleine", "Große", "Lange", "Kurze", "Hohe"]

    def __init__(self, lexicon: Any = None):
        """Initialize with optional lexicon."""
        self.lexicon = lexicon

    def generate(self) -> str:
        """Generate a German street name."""
        pattern = random.choices(
            ["base", "compound", "genitive", "prep", "date", "numeric", "abbrev", "adj"],
            weights=[0.35, 0.15, 0.08, 0.18, 0.04, 0.05, 0.07, 0.08],
        )[0]

        if pattern == "base":
            return self._gen_base()
        elif pattern == "compound":
            return self._gen_compound()
        elif pattern == "genitive":
            return self._gen_genitive()
        elif pattern == "prep":
            return self._gen_prepositional()
        elif pattern == "date":
            return self._gen_date_memorial()
        elif pattern == "numeric":
            return self._gen_numeric()
        elif pattern == "abbrev":
            return self._gen_abbreviated()
        else:
            return self._gen_adjective()

    def _get_name(self) -> str:
        if self.lexicon and hasattr(self.lexicon, 'street_names') and self.lexicon.street_names:
            return random.choice(self.lexicon.street_names)
        return random.choice(self.NAMES)

    def _get_suffix(self) -> str:
        if self.lexicon and hasattr(self.lexicon, 'street_suffixes') and self.lexicon.street_suffixes:
            return random.choice(self.lexicon.street_suffixes)
        return random.choice(self.SUFFIXES)

    def _get_location_noun(self) -> Tuple[str, str]:
        return random.choice(self.LOCATION_NOUNS)

    def _gen_base(self) -> str:
        """Goethestraße, Bachweg"""
        name = self._get_name()
        suffix = self._get_suffix()
        return f"{name}{suffix}"

    def _gen_compound(self) -> str:
        """Karl-Marx-Straße, Heinrich-Heine-Allee"""
        names = [self._get_name() for _ in range(random.randint(2, 3))]
        suffix = self._get_suffix().capitalize()
        return "-".join(names) + "-" + suffix

    def _gen_genitive(self) -> str:
        """Goethes Weg, Schillers Platz (rare but exists)"""
        name = self._get_name()
        suffix = self._get_suffix().capitalize()
        # German genitive: add 's' (or 'ens' for names ending in s/x/z)
        if name[-1] in "sxzß":
            genitive = name + "'"  # Brahms' Weg
        else:
            genitive = name + "s"
        return f"{genitive} {suffix}"

    def _gen_prepositional(self) -> str:
        """Am Markt, An der Brücke, Zur Linde"""
        noun, gender = self._get_location_noun()
        prep_options = self.PREPS_DATIVE.get(gender, self.PREPS_DATIVE["m"])
        prep, _ = random.choice(prep_options)
        return f"{prep} {noun}"

    def _gen_date_memorial(self) -> str:
        """Straße des 17. Juni, Platz des 18. März"""
        suffix = self._get_suffix().capitalize()
        day = random.randint(1, 28)
        months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                  "Juli", "August", "September", "Oktober", "November", "Dezember"]
        month = random.choice(months)
        return f"{suffix} des {day}. {month}"

    def _gen_numeric(self) -> str:
        """1. Straße, 3. Querstraße (American-style grid naming, rare in Germany)"""
        num = random.randint(1, 12)
        suffix = self._get_suffix().capitalize()
        return f"{num}. {suffix}"

    def _gen_abbreviated(self) -> str:
        """Goethe-Str., Bach Str."""
        name = self._get_name()
        if random.random() < 0.5:
            return f"{name}-Str."
        return f"{name} Str."

    def _gen_adjective(self) -> str:
        """Alte Straße, Neue Gasse, Lange Reihe"""
        adj = random.choice(self.ADJECTIVES)
        suffix = self._get_suffix().capitalize()
        return f"{adj} {suffix}"


# Keep the old PCFG for backwards compatibility, but prefer GermanStreetGenerator
GERMAN_STREET_GRAMMAR = {
    "STREET": [
        (["STREET_BASE"], 0.35),
        (["STREET_COMPOUND"], 0.15),
        (["STREET_PREP"], 0.20),
        (["STREET_ABBREV"], 0.10),
        (["STREET_ADJ"], 0.10),
        (["STREET_NUMERIC"], 0.10),
    ],
    "STREET_BASE": [(["NAME", "SUFFIX"], 1.0)],
    "STREET_COMPOUND": [(["NAME", "NAME", "SUFFIX"], 1.0)],
    "STREET_PREP": [(["PREP", "NOUN"], 1.0)],
    "STREET_ABBREV": [(["NAME", "Str."], 1.0)],
    "STREET_ADJ": [(["ADJ", "SUFFIX"], 1.0)],
    "STREET_NUMERIC": [(["NUM", "SUFFIX"], 1.0)],
}