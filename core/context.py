"""Document context for maintaining temporal and logical consistency.

Ensures generated documents have coherent:
- Birth dates matching ages
- Admission/discharge date sequences
- Exam dates within reasonable ranges
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, Dict, Any


@dataclass
class DocumentContext:
    """Maintains consistency across generated document elements.

    All dates and ages are derived from a consistent timeline:
    - patient_birth: Fixed birth date
    - document_date: The "present" date for the document
    - admission_date: When patient was admitted (if applicable)
    - discharge_date: When patient was/will be discharged

    Example:
        ctx = DocumentContext.generate()
        print(ctx.patient_age)        # e.g., 67
        print(ctx.birth_date_str)     # e.g., "15.03.1957"
        print(ctx.admission_date_str) # e.g., "10.01.2024"
    """

    patient_birth: date
    document_date: date
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    exam_date: Optional[date] = None
    gender: str = "male"

    # Cached formatted strings
    _cache: Dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def generate(
        cls,
        min_age: int = 25,
        max_age: int = 85,
        document_year: int = None,
        is_inpatient: bool = True,
        gender: str = None,
    ) -> "DocumentContext":
        """Generate a consistent document context.

        Args:
            min_age: Minimum patient age.
            max_age: Maximum patient age.
            document_year: Year of the document (default: current/recent).
            is_inpatient: Generate admission/discharge dates.
            gender: Patient gender ('male', 'female', or None for random).

        Returns:
            DocumentContext with consistent dates.
        """
        # Document date (the "present")
        if document_year is None:
            document_year = random.choice([2023, 2024, 2025])
        document_month = random.randint(1, 12)
        document_day = random.randint(1, 28)
        document_date = date(document_year, document_month, document_day)

        # Patient age and birth date
        age = random.randint(min_age, max_age)
        birth_year = document_year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)

        # Adjust if birthday hasn't happened yet this year
        if (birth_month, birth_day) > (document_month, document_day):
            birth_year -= 1

        patient_birth = date(birth_year, birth_month, birth_day)

        # Gender
        if gender is None:
            gender = random.choice(["male", "female"])

        ctx = cls(
            patient_birth=patient_birth,
            document_date=document_date,
            gender=gender,
        )

        # Inpatient dates
        if is_inpatient:
            # Admission: 1-14 days before document date
            days_admitted = random.randint(1, 14)
            ctx.admission_date = document_date - timedelta(days=days_admitted)

            # Discharge: 0-7 days after document date (may be planned)
            days_to_discharge = random.randint(0, 7)
            ctx.discharge_date = document_date + timedelta(days=days_to_discharge)

            # Exam date: during admission
            exam_offset = random.randint(0, days_admitted)
            ctx.exam_date = ctx.admission_date + timedelta(days=exam_offset)
        else:
            # Outpatient: exam is the document date
            ctx.exam_date = document_date

        return ctx

    @property
    def patient_age(self) -> int:
        """Calculate patient's age at document date."""
        age = self.document_date.year - self.patient_birth.year
        # Adjust if birthday hasn't happened yet
        if (self.patient_birth.month, self.patient_birth.day) > \
           (self.document_date.month, self.document_date.day):
            age -= 1
        return age

    def _format_date(self, d: date) -> str:
        """Format date as DD.MM.YYYY (German style)."""
        return f"{d.day:02d}.{d.month:02d}.{d.year}"

    @property
    def birth_date_str(self) -> str:
        """Birth date as German-formatted string."""
        return self._format_date(self.patient_birth)

    @property
    def document_date_str(self) -> str:
        """Document date as German-formatted string."""
        return self._format_date(self.document_date)

    @property
    def admission_date_str(self) -> Optional[str]:
        """Admission date as German-formatted string."""
        if self.admission_date:
            return self._format_date(self.admission_date)
        return None

    @property
    def discharge_date_str(self) -> Optional[str]:
        """Discharge date as German-formatted string."""
        if self.discharge_date:
            return self._format_date(self.discharge_date)
        return None

    @property
    def exam_date_str(self) -> Optional[str]:
        """Exam date as German-formatted string."""
        if self.exam_date:
            return self._format_date(self.exam_date)
        return None

    @property
    def age_description(self) -> str:
        """Age as German adjective form (e.g., '67-jährig')."""
        return f"{self.patient_age}-jährig"

    @property
    def age_variants(self) -> list:
        """Multiple age expression variants."""
        age = self.patient_age
        return [
            f"{age}-jährig",
            f"{age}-jährigen",
            f"{age} Jahre alt",
            f"{age} J.",
        ]

    @property
    def stay_duration_days(self) -> Optional[int]:
        """Length of hospital stay in days."""
        if self.admission_date and self.discharge_date:
            return (self.discharge_date - self.admission_date).days
        return None

    @property
    def patient_salutation(self) -> str:
        """German salutation based on gender."""
        return "Herr" if self.gender == "male" else "Frau"

    @property
    def patient_salutation_abbr(self) -> str:
        """Abbreviated German salutation."""
        return "Hr." if self.gender == "male" else "Fr."

    def to_template_context(self) -> Dict[str, Any]:
        """Export as dict for template substitution.

        Returns values compatible with template engine placeholders.
        """
        return {
            "birth": self.birth_date_str,
            "age": self.age_description,
            "date": self.document_date_str,
            "admission": self.admission_date_str,
            "discharge": self.discharge_date_str,
            "exam": self.exam_date_str,
            "gender": self.gender,
            "salutation": self.patient_salutation,
        }
