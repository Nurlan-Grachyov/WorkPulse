from abc import ABC, abstractmethod
from datetime import date, datetime


class CalendarPeriod(ABC):
    @abstractmethod
    def get_range(self, today: date) -> tuple[datetime, datetime]: ...
