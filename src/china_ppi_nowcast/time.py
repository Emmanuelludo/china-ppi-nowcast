"""China Standard Time and ten-day release-window logic."""

from __future__ import annotations

import calendar
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from .schema import Window

CHINA_TZ = ZoneInfo("Asia/Shanghai")

WINDOW_CN = {"上旬": Window.FIRST, "中旬": Window.SECOND, "下旬": Window.THIRD}


def parse_as_of(value: str | datetime) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("as_of must include an explicit timezone offset")
    return dt.astimezone(CHINA_TZ)


def parse_target_month(value: str) -> pd.Period:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("target_month must use YYYY-MM")
    return pd.Period(value, freq="M")


def parse_release_title(title: str) -> tuple[str, Window] | None:
    match = re.search(r"(20\d{2})年(\d{1,2})月(上旬|中旬|下旬).*流通领域重要生产资料", title)
    if not match:
        return None
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}", WINDOW_CN[match.group(3)]


def target_vintage(target_month: str, available_windows: set[tuple[str, str]]) -> str:
    month = parse_target_month(target_month)
    prior = str(month - 1)
    has_carry = (prior, Window.THIRD.value) in available_windows
    has_first = (str(month), Window.FIRST.value) in available_windows
    has_second = (str(month), Window.SECOND.value) in available_windows
    if has_carry and has_first and has_second:
        return "final"
    if has_carry and has_first:
        return "early"
    return "not_ready"


def default_target_month(now: datetime) -> str:
    return now.astimezone(CHINA_TZ).strftime("%Y-%m")


def window_end_date(month: str, window: Window) -> str:
    period = parse_target_month(month)
    if window is Window.FIRST:
        day = 10
    elif window is Window.SECOND:
        day = 20
    else:
        day = calendar.monthrange(period.year, period.month)[1]
    return f"{period.year:04d}-{period.month:02d}-{day:02d}"
