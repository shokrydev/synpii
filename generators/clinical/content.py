"""Clinical content generators (non-PII medical data)."""

import random
from typing import List, Optional

from synpii.generators.base import BaseGenerator


class ClinicalContentGenerator:
    """Generate non-PII clinical content.

    Provides realistic medical filler content for templates:
    - Diagnoses
    - Symptoms
    - Medications
    - Departments
    - Specialties
    - Duration phrases

    Note: This doesn't inherit from BaseGenerator as it produces
    non-PII content that doesn't need annotation tracking.
    """

    # Medical departments
    DEPARTMENTS = [
        "Inneren Medizin", "Chirurgie", "Kardiologie", "Neurologie",
        "Orthopädie", "Gastroenterologie", "Notaufnahme", "Urologie",
        "Gynäkologie", "Pädiatrie", "Psychiatrie", "Dermatologie",
    ]

    # Medical specialties
    SPECIALTIES = [
        "Innere Medizin", "Allgemeinmedizin", "Kardiologie", "Chirurgie",
        "Neurologie", "Orthopädie", "Radiologie", "Anästhesiologie",
        "Urologie", "Gynäkologie", "Psychiatrie", "Dermatologie",
    ]

    # Duration phrases
    DURATIONS = [
        "zwei Wochen", "drei Wochen", "einem Monat", "sechs Wochen",
        "zwei Monaten", "mehreren Wochen", "einigen Tagen", "wenigen Tagen",
        "circa einer Woche", "etwa zehn Tagen",
    ]

    # Wound locations
    WOUND_LOCATIONS = [
        "rechten Unterarm", "linken Oberschenkel", "Abdomen",
        "rechten Knie", "linken Fuß", "Rücken", "rechten Schulter",
        "linken Unterschenkel", "Bauchdecke", "Leiste",
    ]

    # Clinical findings
    FINDINGS = [
        "Laborchemisch zeigt sich eine leichte Erhöhung der Entzündungsparameter.",
        "Sonographisch regelrechter Befund ohne pathologische Auffälligkeiten.",
        "EKG: Sinusrhythmus, keine ST-Streckenveränderungen.",
        "Röntgen Thorax: Keine pneumonischen Infiltrate.",
        "Unauffälliger körperlicher Untersuchungsbefund.",
        "CT-Abdomen: Kein Nachweis freier Flüssigkeit.",
        "MRT-Schädel: Altersentsprechender Normalbefund.",
        "Duplexsonographie: Regelrechter Befund ohne Hinweis auf TVT.",
    ]

    # Assessments
    ASSESSMENTS = [
        "Kein Hinweis auf akute Pathologie.",
        "Befund vereinbar mit der klinischen Verdachtsdiagnose.",
        "Kontrollbedürftiger Befund, Wiedervorstellung empfohlen.",
        "Altersentsprechender Normalbefund.",
        "Befund unter Therapie rückläufig.",
    ]

    # Therapy descriptions
    THERAPIES = [
        "Es erfolgte eine medikamentöse Einstellung mit Ramipril 5mg 1-0-0.",
        "Die antibiotische Therapie mit Amoxicillin wurde für 7 Tage fortgeführt.",
        "Physiotherapeutische Behandlung wurde eingeleitet.",
        "Schmerztherapie nach WHO-Stufenschema.",
        "Operative Versorgung am Aufnahmetag komplikationslos.",
        "Infusionstherapie mit Vollelektrolytlösung.",
        "Thromboseprophylaxe mit niedermolekularem Heparin.",
    ]

    def __init__(self, lexicon=None):
        """Initialize content generator.

        Args:
            lexicon: Optional GermanLexicon for additional values.
        """
        self.lexicon = lexicon

    def get_diagnosis(self) -> str:
        """Get a random diagnosis."""
        if self.lexicon is not None and self.lexicon.diagnoses:
            return random.choice(self.lexicon.diagnoses)
        return random.choice([
            "Arterielle Hypertonie", "Diabetes mellitus Typ 2",
            "KHK", "COPD", "Herzinsuffizienz NYHA II",
            "Vorhofflimmern", "Pneumonie", "Lumboischialgie",
        ])

    def get_symptom(self) -> str:
        """Get a random symptom."""
        if self.lexicon is not None and self.lexicon.symptoms:
            return random.choice(self.lexicon.symptoms)
        return random.choice([
            "Brustschmerzen", "Atemnot", "Schwindel", "Übelkeit",
            "Kopfschmerzen", "Rückenschmerzen", "Müdigkeit",
        ])

    def get_medication(self) -> str:
        """Get a random medication."""
        if self.lexicon is not None and self.lexicon.medications:
            return random.choice(self.lexicon.medications)
        return random.choice([
            "Ramipril 5mg", "Metoprolol 47,5mg", "Amlodipin 5mg",
            "Simvastatin 20mg", "Metformin 500mg", "L-Thyroxin 50µg",
        ])

    def get_occupation(self) -> str:
        """Get a random occupation."""
        if self.lexicon is not None and self.lexicon.occupations:
            return random.choice(self.lexicon.occupations)
        return random.choice([
            "Rentner", "Rentnerin", "Angestellter", "Angestellte",
            "Selbstständiger", "Lehrer", "Lehrerin",
        ])

    def get_department(self) -> str:
        """Get a random department name."""
        return random.choice(self.DEPARTMENTS)

    def get_specialty(self) -> str:
        """Get a random medical specialty."""
        return random.choice(self.SPECIALTIES)

    def get_duration(self) -> str:
        """Get a random duration phrase."""
        return random.choice(self.DURATIONS)

    def get_wound_location(self) -> str:
        """Get a random wound location."""
        return random.choice(self.WOUND_LOCATIONS)

    def get_finding(self) -> str:
        """Get a random clinical finding."""
        return random.choice(self.FINDINGS)

    def get_assessment(self) -> str:
        """Get a random clinical assessment."""
        return random.choice(self.ASSESSMENTS)

    def get_therapy(self) -> str:
        """Get a random therapy description."""
        return random.choice(self.THERAPIES)

    def get_ward(self) -> str:
        """Get a random ward identifier."""
        return f"Station {random.randint(1, 12)}"

    def get_vital_signs(self) -> dict:
        """Generate random vital signs."""
        return {
            "bp_systolic": random.randint(110, 160),
            "bp_diastolic": random.randint(60, 95),
            "pulse": random.randint(55, 100),
            "temperature": round(random.uniform(36.0, 38.5), 1),
            "spo2": random.randint(92, 100),
        }
