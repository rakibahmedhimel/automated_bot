from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def get_company_now(timezone: str) -> datetime:
    return datetime.now(ZoneInfo(timezone))


def get_company_today(timezone: str) -> date:
    return get_company_now(timezone).date()


def is_past_date(
    requested_date: date,
    timezone: str,
) -> bool:
    return requested_date < get_company_today(timezone)


def is_past_datetime(
    requested_date: date,
    requested_time: time,
    timezone: str,
) -> bool:
    requested_datetime = datetime.combine(
        requested_date,
        requested_time,
        tzinfo=ZoneInfo(timezone),
    )

    return requested_datetime < get_company_now(timezone)


def validate_future_date(
    requested_date: date,
    timezone: str,
) -> None:
    if is_past_date(requested_date, timezone):
        raise ValueError(
            "The requested date cannot be in the past"
        )


def validate_future_datetime(
    requested_date: date,
    requested_time: time,
    timezone: str,
) -> None:
    if is_past_datetime(
        requested_date,
        requested_time,
        timezone,
    ):
        raise ValueError(
            "The requested time cannot be in the past"
        )