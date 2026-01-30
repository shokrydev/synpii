"""Lexicon management with German grammar awareness.

Provides:
- ValueLoader: Generic file-based value loading with metadata support
- GermanLexicon: German-specific lexicon with gender/case agreement
"""

import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union


class ValueLoader:
    """Load values from external text files with optional metadata.

    Supports:
    - Simple line-per-value format
    - Pipe-delimited metadata (value|meta1|meta2)
    - Comment lines starting with #
    - UTF-8 encoding for German umlauts

    Example files:
        # names/first_names_male.txt
        Hans
        Peter
        Wolfgang

        # locations/nouns_with_gender.txt (with metadata)
        Wald|m|0.15
        Brücke|f|0.08
        Ufer|n|0.07
    """

    def __init__(self, values_dir: Path):
        """Initialize loader with values directory.

        Args:
            values_dir: Path to directory containing value files.
        """
        self.values_dir = Path(values_dir)
        self._cache: Dict[str, List] = {}

    def load(self, path: str, with_metadata: bool = False) -> List:
        """Load values from file.

        Args:
            path: Relative path like "names/first_names_male.txt"
            with_metadata: If True, parse "value|meta1|meta2" format

        Returns:
            List of values or list of [value, meta1, meta2, ...] lists
        """
        cache_key = f"{path}:{with_metadata}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        full_path = self.values_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"Values file not found: {full_path}")

        lines = full_path.read_text(encoding="utf-8").strip().split("\n")
        lines = [line.strip() for line in lines if line.strip() and not line.startswith("#")]

        if with_metadata:
            values = [line.split("|") for line in lines]
        else:
            # For non-metadata, still handle potential pipe-delimited files
            # by taking only the first part
            values = [line.split("|")[0] for line in lines]

        self._cache[cache_key] = values
        return values

    def sample(self, path: str, with_metadata: bool = False) -> Union[str, List[str]]:
        """Random sample from file.

        Args:
            path: Relative path to values file.
            with_metadata: If True, return full metadata list.

        Returns:
            Random value or [value, meta1, meta2, ...] list.
        """
        values = self.load(path, with_metadata)
        return random.choice(values) if values else None

    def sample_weighted(self, path: str, weight_index: int = 2) -> str:
        """Sample using weights from metadata.

        Args:
            path: Relative path to values file.
            weight_index: Index of weight in metadata (default: 2 for value|gender|weight).

        Returns:
            Weighted random value.
        """
        values = self.load(path, with_metadata=True)
        if not values:
            return None

        # Parse weights
        weighted_values = []
        for item in values:
            value = item[0]
            try:
                weight = float(item[weight_index]) if len(item) > weight_index else 1.0
            except (ValueError, IndexError):
                weight = 1.0
            weighted_values.append((value, weight))

        # Weighted selection
        total_weight = sum(w for _, w in weighted_values)
        if total_weight == 0:
            return random.choice([v for v, _ in weighted_values])

        r = random.random() * total_weight
        cumulative = 0.0
        for value, weight in weighted_values:
            cumulative += weight
            if r <= cumulative:
                return value

        return weighted_values[-1][0]

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()


class GermanLexicon:
    """German-specific lexicon with grammar awareness.

    Handles:
    - Noun gender (m/f/n/pl)
    - Article agreement (der/die/das, dem/der/dem/den)
    - Case declension (nominative, genitive, dative, accusative)

    German definite articles:
        Case        m       f       n       pl
        Nominative  der     die     das     die
        Genitive    des     der     des     der
        Dative      dem     der     dem     den
        Accusative  den     die     das     die
    """

    # Article tables
    DEFINITE_ARTICLES = {
        "nominative": {"m": "der", "f": "die", "n": "das", "pl": "die"},
        "genitive": {"m": "des", "f": "der", "n": "des", "pl": "der"},
        "dative": {"m": "dem", "f": "der", "n": "dem", "pl": "den"},
        "accusative": {"m": "den", "f": "die", "n": "das", "pl": "die"},
    }

    INDEFINITE_ARTICLES = {
        "nominative": {"m": "ein", "f": "eine", "n": "ein", "pl": ""},
        "genitive": {"m": "eines", "f": "einer", "n": "eines", "pl": ""},
        "dative": {"m": "einem", "f": "einer", "n": "einem", "pl": ""},
        "accusative": {"m": "einen", "f": "eine", "n": "ein", "pl": ""},
    }

    # Preposition case requirements
    PREPOSITION_CASES = {
        # Always dative
        "an": "dative", "auf": "dative", "bei": "dative", "in": "dative",
        "unter": "dative", "über": "dative", "vor": "dative", "hinter": "dative",
        "neben": "dative", "zwischen": "dative",
        "aus": "dative", "mit": "dative", "nach": "dative", "seit": "dative",
        "von": "dative", "zu": "dative", "gegenüber": "dative",
        # Always genitive
        "während": "genitive", "wegen": "genitive", "trotz": "genitive",
        "innerhalb": "genitive", "außerhalb": "genitive",
        # Contractions
        "am": "dative", "im": "dative", "zum": "dative", "zur": "dative",
        "beim": "dative", "vom": "dative",
    }

    def __init__(self, values_dir: Path):
        """Initialize lexicon.

        Args:
            values_dir: Path to values directory.
        """
        self.values_dir = Path(values_dir)
        self.loader = ValueLoader(values_dir)

        # Cache for loaded values
        self._first_names_male: List[str] = None
        self._first_names_female: List[str] = None
        self._last_names: List[str] = None
        self._cities: List[Tuple[str, str, str]] = None
        self._street_names: List[str] = None
        self._street_suffixes: List[str] = None
        self._location_nouns: List[Dict[str, Any]] = None
        self._hospitals: List[str] = None
        self._diagnoses: List[str] = None
        self._symptoms: List[str] = None
        self._occupations: List[str] = None
        self._insurance_companies: List[str] = None
        self._medications: List[str] = None

    # --- Name properties ---

    @property
    def first_names_male(self) -> List[str]:
        if self._first_names_male is None:
            self._first_names_male = self.loader.load("names/first_names_male.txt")
        return self._first_names_male

    @property
    def first_names_female(self) -> List[str]:
        if self._first_names_female is None:
            self._first_names_female = self.loader.load("names/first_names_female.txt")
        return self._first_names_female

    @property
    def last_names(self) -> List[str]:
        if self._last_names is None:
            self._last_names = self.loader.load("names/last_names.txt")
        return self._last_names

    # --- Location properties ---

    @property
    def cities(self) -> List[Tuple[str, str, str]]:
        """Load cities with PLZ ranges: [(name, plz_min, plz_max), ...]"""
        if self._cities is None:
            raw = self.loader.load("locations/cities.txt", with_metadata=True)
            self._cities = [(item[0], item[1], item[2]) for item in raw if len(item) >= 3]
        return self._cities

    @property
    def street_names(self) -> List[str]:
        if self._street_names is None:
            self._street_names = self.loader.load("locations/street_names.txt")
        return self._street_names

    @property
    def street_suffixes(self) -> List[str]:
        if self._street_suffixes is None:
            try:
                self._street_suffixes = self.loader.load("locations/street_suffixes.txt")
            except FileNotFoundError:
                # Default suffixes if file not found
                self._street_suffixes = [
                    "straße", "weg", "allee", "platz", "ring", "gasse",
                    "damm", "ufer", "bach", "kanal", "hof", "stieg", "markt",
                ]
        return self._street_suffixes

    @property
    def location_nouns(self) -> List[Dict[str, Any]]:
        """Load location nouns with gender: [{"word": ..., "gender": ..., "freq": ...}, ...]"""
        if self._location_nouns is None:
            try:
                raw = self.loader.load("locations/nouns_with_gender.txt", with_metadata=True)
                self._location_nouns = []
                for item in raw:
                    entry = {
                        "word": item[0],
                        "gender": item[1] if len(item) > 1 else "m",
                        "freq": float(item[2]) if len(item) > 2 else 1.0,
                    }
                    self._location_nouns.append(entry)
            except FileNotFoundError:
                # Default nouns if file not found
                self._location_nouns = [
                    {"word": "Wald", "gender": "m", "freq": 0.15},
                    {"word": "Brücke", "gender": "f", "freq": 0.08},
                    {"word": "Ufer", "gender": "n", "freq": 0.07},
                    {"word": "Markt", "gender": "m", "freq": 0.12},
                    {"word": "Kirche", "gender": "f", "freq": 0.10},
                    {"word": "Wiese", "gender": "f", "freq": 0.08},
                ]
        return self._location_nouns

    # --- Clinical/medical properties ---

    @property
    def hospitals(self) -> List[str]:
        if self._hospitals is None:
            self._hospitals = self.loader.load("organizations/hospitals.txt")
        return self._hospitals

    @property
    def diagnoses(self) -> List[str]:
        if self._diagnoses is None:
            self._diagnoses = self.loader.load("clinical/diagnoses.txt")
        return self._diagnoses

    @property
    def symptoms(self) -> List[str]:
        if self._symptoms is None:
            try:
                self._symptoms = self.loader.load("clinical/symptoms.txt")
            except FileNotFoundError:
                self._symptoms = []
        return self._symptoms

    @property
    def medications(self) -> List[str]:
        if self._medications is None:
            try:
                self._medications = self.loader.load("clinical/medications.txt")
            except FileNotFoundError:
                self._medications = []
        return self._medications

    @property
    def occupations(self) -> List[str]:
        if self._occupations is None:
            try:
                self._occupations = self.loader.load("clinical/occupations.txt")
            except FileNotFoundError:
                self._occupations = []
        return self._occupations

    @property
    def insurance_companies(self) -> List[str]:
        if self._insurance_companies is None:
            try:
                self._insurance_companies = self.loader.load("organizations/insurance_companies.txt")
            except FileNotFoundError:
                self._insurance_companies = []
        return self._insurance_companies

    # --- Grammar helpers ---

    def get_article(
        self,
        gender: str,
        case: str = "nominative",
        definite: bool = True,
    ) -> str:
        """Get the correct article for gender and case.

        Args:
            gender: 'm', 'f', 'n', or 'pl'
            case: 'nominative', 'genitive', 'dative', or 'accusative'
            definite: True for definite article, False for indefinite

        Returns:
            The appropriate article.
        """
        articles = self.DEFINITE_ARTICLES if definite else self.INDEFINITE_ARTICLES
        return articles.get(case, {}).get(gender, "")

    def get_preposition_case(self, preposition: str) -> str:
        """Get the case required by a preposition.

        Args:
            preposition: German preposition (e.g., "an", "mit", "während")

        Returns:
            Required case: 'dative', 'genitive', or 'accusative'
        """
        # Normalize (lowercase, handle contractions)
        prep_lower = preposition.lower()
        return self.PREPOSITION_CASES.get(prep_lower, "dative")

    def sample_location_noun(self, with_article: bool = False, case: str = "dative") -> str:
        """Sample a location noun, optionally with correct article.

        Args:
            with_article: Include definite article.
            case: Grammatical case for article.

        Returns:
            Location noun, optionally with article.
        """
        if not self.location_nouns:
            return "Markt"

        # Weighted selection
        total_freq = sum(n["freq"] for n in self.location_nouns)
        r = random.random() * total_freq
        cumulative = 0.0

        for noun_data in self.location_nouns:
            cumulative += noun_data["freq"]
            if r <= cumulative:
                word = noun_data["word"]
                if with_article:
                    article = self.get_article(noun_data["gender"], case)
                    return f"{article} {word}"
                return word

        # Fallback
        noun_data = self.location_nouns[-1]
        word = noun_data["word"]
        if with_article:
            article = self.get_article(noun_data["gender"], case)
            return f"{article} {word}"
        return word

    # --- Sampling helpers ---

    def sample_first_name(self, gender: str = None) -> str:
        """Sample a random first name.

        Args:
            gender: 'male', 'female', or None for random.

        Returns:
            First name string.
        """
        if gender is None:
            gender = random.choice(["male", "female"])

        if gender == "male":
            return random.choice(self.first_names_male)
        else:
            return random.choice(self.first_names_female)

    def sample_last_name(self) -> str:
        """Sample a random last name."""
        return random.choice(self.last_names)

    def sample_city(self) -> Tuple[str, str, str]:
        """Sample a city with PLZ range: (name, plz_min, plz_max)."""
        return random.choice(self.cities)

    def sample_street_name(self) -> str:
        """Sample a street name prefix."""
        return random.choice(self.street_names)

    def sample_street_suffix(self) -> str:
        """Sample a street suffix."""
        return random.choice(self.street_suffixes)
