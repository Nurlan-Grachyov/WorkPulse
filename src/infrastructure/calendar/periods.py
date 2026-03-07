from datetime import date, datetime, timedelta

from src.domain.calendar.service import CalendarPeriod


class DayPeriod(CalendarPeriod):
    def get_range(self, today: date) -> tuple[datetime, datetime]:
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        return start, end


class MonthPeriod(CalendarPeriod):
    def get_range(self, today: date) -> tuple[datetime, datetime]:
        start_date = today.replace(day=1)
        next_month = (start_date + timedelta(days=31)).replace(day=1)
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(next_month, datetime.min.time())
        return start, end
