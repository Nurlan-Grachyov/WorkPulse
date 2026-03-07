from src.domain.calendar.service import CalendarPeriod
from src.infrastructure.calendar.periods import DayPeriod, MonthPeriod


class CalendarPeriodFactory:
    _periods: dict[str, type[CalendarPeriod]] = {
        "day": DayPeriod,
        "month": MonthPeriod,
    }

    @classmethod
    def create(cls, period: str) -> CalendarPeriod:
        try:
            period_cls = cls._periods[period]
        except KeyError:
            raise ValueError("unsupported_period")
        return period_cls()
