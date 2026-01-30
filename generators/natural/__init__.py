"""Natural language entity generators (person, location, date, etc.)."""

from synpii.generators.natural.person import PersonGenerator
from synpii.generators.natural.location import LocationGenerator
from synpii.generators.natural.date import DateGenerator
from synpii.generators.natural.contact import PhoneGenerator, EmailGenerator
from synpii.generators.natural.age import AgeGenerator

__all__ = [
    "PersonGenerator",
    "LocationGenerator",
    "DateGenerator",
    "PhoneGenerator",
    "EmailGenerator",
    "AgeGenerator",
]
