"""German date generator with multiple format variants."""

import random
from datetime import date, timedelta
from typing import Optional

from synpii.core.types import Entity
from synpii.generators.base import BaseGenerator


class DateGenerator(BaseGenerator):
    """Generate German-formatted dates.

    Supports:
    - Birth dates (1940-2005)
    - Recent dates (recent years)
    - Admission/discharge dates
    - Multiple format variants
    """

    entity_types = ["DATE_TIME"]

    MONTH_NAMES = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]

    MONTH_NAMES_SHORT = [
        "Jan.", "Feb.", "März", "Apr.", "Mai", "Juni",
        "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez.",
    ]

    def generate(
        self,
        date_type: str = "birth",
        year_range: tuple = None,
        **kwargs,
    ) -> Entity:
        """Generate a German-formatted date.

        Args:
            date_type: 'birth', 'recent', 'admission', or 'any'.
            year_range: Optional (min_year, max_year) tuple.
            **kwargs: Additional parameters.

        Returns:
            Entity with date value.
        """
        # Determine year range
        if year_range:
            min_year, max_year = year_range
        elif date_type == "birth":
            min_year, max_year = 1940, 2005
        elif date_type == "recent":
            min_year, max_year = 2023, 2025
        elif date_type == "admission":
            min_year, max_year = 2023, 2025
        else:
            min_year, max_year = 2000, 2025

        # Generate date components
        year = random.randint(min_year, max_year)
        month = random.randint(1, 12)
        # Ensure valid day for month
        if month in [4, 6, 9, 11]:
            max_day = 30
        elif month == 2:
            # Simplified leap year check
            max_day = 29 if year % 4 == 0 else 28
        else:
            max_day = 31
        day = random.randint(1, max_day)

        # Primary format: DD.MM.YYYY
        date_str = f"{day:02d}.{month:02d}.{year}"

        # Build variants
        month_name = self.MONTH_NAMES[month - 1]
        month_short = self.MONTH_NAMES_SHORT[month - 1]

        variants = [
            date_str,                                    # 15.03.1990
            f"{day}. {month_name} {year}",              # 15. März 1990
            f"{day}.{month}.{year}",                    # 15.3.1990
            f"{day:02d}/{month:02d}/{year}",            # 15/03/1990
            f"{day}. {month_short} {year}",             # 15. März 1990
            f"am {day}. {month_name}",                  # am 15. März
            f"{month_name} {year}",                     # März 1990
            f"{day}.{month:02d}.{year}",                # 15.03.1990 (no leading zero on day)
        ]

        # Add ISO format for variety
        variants.append(f"{year}-{month:02d}-{day:02d}")

        return Entity(
            entity_type="DATE_TIME",
            value=date_str,
            variants=variants,
            metadata={
                "day": day,
                "month": month,
                "year": year,
                "date_type": date_type,
            },
        )

    def generate_date_range(
        self,
        start_date: Entity = None,
        days_between: tuple = (1, 14),
        **kwargs,
    ) -> tuple:
        """Generate two related dates (e.g., admission and discharge).

        Args:
            start_date: Optional start date entity.
            days_between: (min_days, max_days) between dates.
            **kwargs: Additional parameters.

        Returns:
            Tuple of (start_entity, end_entity).
        """
        if start_date is None:
            start_date = self.generate(date_type="recent", **kwargs)

        # Parse start date
        day = start_date.metadata["day"]
        month = start_date.metadata["month"]
        year = start_date.metadata["year"]

        # Calculate end date
        start = date(year, month, day)
        days_diff = random.randint(*days_between)
        end = start + timedelta(days=days_diff)

        # Generate end date entity
        end_str = f"{end.day:02d}.{end.month:02d}.{end.year}"
        month_name = self.MONTH_NAMES[end.month - 1]

        end_entity = Entity(
            entity_type="DATE_TIME",
            value=end_str,
            variants=[
                end_str,
                f"{end.day}. {month_name} {end.year}",
                f"{end.day}.{end.month}.{end.year}",
            ],
            metadata={
                "day": end.day,
                "month": end.month,
                "year": end.year,
                "date_type": "discharge",
            },
        )

        return start_date, end_entity
