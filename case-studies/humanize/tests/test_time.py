"""humanize time functions, rewritten with plainly.

Differences from the upstream tests, all aimed at the reviewer:
  * a past moment is written as a plain timedelta ("30 seconds ago"), so most rows
    need no frozen clock; only naturalday/naturaldate really depend on "today".
  * future moments are written as `NOW + timedelta(...)` with an explicit `when=NOW`.
"""

import datetime as dt

import humanize
from freezegun import freeze_time
from humanize import naturalday, naturaldate, naturaldelta, naturaltime, precisedelta, time

from plainly import expect, spec

td = dt.timedelta
NOW = dt.datetime(2010, 2, 2)
NOW_UTC = dt.datetime(2010, 2, 2, tzinfo=dt.timezone.utc)
TODAY = dt.date(2010, 2, 2)
TOMORROW, YESTERDAY = TODAY + td(days=1), TODAY - td(days=1)

ONE_MICROSECOND, FOUR_MICROSECONDS = 1 / 1_000_000, 4 / 1_000_000
ONE_MILLISECOND, FOUR_MILLISECONDS = 1 / 1000, 4 / 1000
MICROSECONDS_101_943 = 101943 / 1_000_000  # 101.94 milliseconds
MILLISECONDS_1_337 = 1337 / 1000  # 1.337 seconds
ONE_HOUR = 3600
ONE_DAY = 24 * ONE_HOUR
ONE_YEAR = 365.25 * ONE_DAY


def later(**delta):
    return NOW + td(**delta)


# ===== naturaldelta =========================================================


def test_naturaldelta_rounds_to_the_nearest_sensible_unit():
    rule = spec(naturaldelta)
    rule.if_(0).then_give("a moment")
    rule.if_(1).then_give("a second")
    rule.if_(23.5).then_give("23 seconds")
    rule.if_(30).then_give("30 seconds")
    rule.if_(td(microseconds=13)).then_give("a moment")
    rule.if_(td(seconds=1)).then_give("a second")
    rule.if_(td(seconds=30)).then_give("30 seconds")
    rule.if_(td(minutes=1, seconds=29)).then_give("a minute")
    rule.if_(td(minutes=1, seconds=30)).then_give("2 minutes")
    rule.if_(td(minutes=1, seconds=59)).then_give("2 minutes")
    rule.if_(td(minutes=2)).then_give("2 minutes")
    rule.if_(td(minutes=59)).then_give("59 minutes")
    rule.if_(td(minutes=59, seconds=30)).then_give("an hour")
    rule.if_(td(hours=1, minutes=29)).then_give("an hour")
    rule.if_(td(hours=23, minutes=50, seconds=50)).then_give("a day")
    rule.if_(td(days=1)).then_give("a day")


def test_naturaldelta_hours_round_half_to_even():
    # See https://en.wikipedia.org/wiki/IEEE_754#Rounding_rules
    rule = spec(naturaldelta)
    rule.if_(td(hours=1, minutes=30)).then_give("2 hours")
    rule.if_(td(hours=2, minutes=30)).then_give("2 hours")
    rule.if_(td(hours=3, minutes=30)).then_give("4 hours")


def test_naturaldelta_days_months_and_years():
    rule = spec(naturaldelta)
    rule.if_(td(days=9)).then_give("9 days")
    rule.if_(td(days=35)).then_give("a month")
    rule.if_(td(days=65)).then_give("2 months")
    rule.if_(td(days=364)).then_give("a year")
    rule.if_(td(days=365)).then_give("a year")
    rule.if_(td(days=365 + 4)).then_give("1 year, 4 days")
    rule.if_(td(days=365 + 35)).then_give("1 year, 1 month")
    rule.if_(td(days=500)).then_give("1 year, 4 months")
    rule.if_(td(days=365 + 364)).then_give("2 years")
    rule.if_(td(days=365 * 2)).then_give("2 years")
    rule.if_(td(days=365 * 2 + 35)).then_give("2 years")
    rule.if_(td(days=365 * 2 + 65)).then_give("2 years")
    rule.if_(td(days=365 * 2.4)).then_give("2 years")
    rule.if_(td(days=365 * 2.6)).then_give("3 years")
    rule.if_(td(days=365 * 2.9)).then_give("3 years")
    rule.if_(td(days=365 * 3)).then_give("3 years")
    rule.if_(td(days=10000)).then_give("27 years")
    rule.if_(td(days=365 * 1_141)).then_give("1,141 years")
    rule.if_(td(days=999_999_999)).then_give("2,739,726 years")  # the largest possible timedelta


def test_naturaldelta_without_months_counts_days_instead():
    rule = spec(naturaldelta)
    rule.if_(td(days=7), months=False).then_give("7 days")
    rule.if_(td(days=31), months=False).then_give("31 days")
    rule.if_(td(days=230), months=False).then_give("230 days")
    rule.if_(td(days=400), months=False).then_give("1 year, 35 days")


def test_naturaldelta_ignores_direction():
    for delta in [td(seconds=30), td(hours=3), td(days=500), td(days=365 * 2 + 35), td(days=10000)]:
        expect(naturaldelta(-delta), f"naturaldelta(-{delta!r})".replace("datetime.", "")).should.be(
            naturaldelta(delta)
        )


def test_naturaldelta_leaves_non_numbers_alone():
    rule = spec(naturaldelta)
    rule.if_("NaN").then_give("NaN")
    rule.if_(None).then_give("None")


def test_naturaldelta_returns_non_finite_floats_unchanged():
    rule = spec(naturaldelta)
    rule.if_(float("nan")).then_give("nan")
    rule.if_(float("inf")).then_give("inf")
    rule.if_(float("-inf")).then_give("-inf")


def test_naturaldelta_too_large_a_finite_value_overflows():
    spec(naturaldelta).if_(1e30).then_raise(OverflowError)


def test_naturaldelta_minimum_unit_defaults_to_seconds():
    rule = spec(naturaldelta)
    rule.if_(td(seconds=ONE_MICROSECOND)).then_give("a moment")
    rule.if_(td(seconds=FOUR_MICROSECONDS)).then_give("a moment")
    rule.if_(td(seconds=ONE_MILLISECOND)).then_give("a moment")
    rule.if_(td(seconds=FOUR_MILLISECONDS)).then_give("a moment")
    rule.if_(td(seconds=2)).then_give("2 seconds")
    rule.if_(td(seconds=4)).then_give("4 seconds")
    rule.if_(td(seconds=ONE_HOUR + FOUR_MILLISECONDS)).then_give("an hour")
    rule.if_(td(seconds=ONE_DAY + FOUR_MILLISECONDS)).then_give("a day")
    rule.if_(td(seconds=ONE_YEAR + FOUR_MICROSECONDS)).then_give("a year")


MINIMUM_UNIT_ROWS = [
    ("seconds", ONE_MICROSECOND, "a moment"),
    ("seconds", FOUR_MICROSECONDS, "a moment"),
    ("seconds", ONE_MILLISECOND, "a moment"),
    ("seconds", FOUR_MILLISECONDS, "a moment"),
    ("seconds", MICROSECONDS_101_943, "a moment"),
    ("seconds", MILLISECONDS_1_337, "a second"),
    ("seconds", 2, "2 seconds"),
    ("seconds", 4, "4 seconds"),
    ("seconds", ONE_HOUR + FOUR_MILLISECONDS, "an hour"),
    ("seconds", ONE_DAY + FOUR_MILLISECONDS, "a day"),
    ("seconds", ONE_YEAR + FOUR_MICROSECONDS, "a year"),
    ("milliseconds", FOUR_MICROSECONDS, "0 milliseconds"),
    ("milliseconds", ONE_MILLISECOND, "1 millisecond"),
    ("milliseconds", FOUR_MILLISECONDS, "4 milliseconds"),
    ("milliseconds", MICROSECONDS_101_943, "101 milliseconds"),
    ("milliseconds", MILLISECONDS_1_337, "a second"),
    ("milliseconds", 2, "2 seconds"),
    ("milliseconds", 4, "4 seconds"),
    ("milliseconds", ONE_HOUR + FOUR_MILLISECONDS, "an hour"),
    ("milliseconds", ONE_YEAR + FOUR_MICROSECONDS, "a year"),
    ("microseconds", ONE_MICROSECOND, "1 microsecond"),
    ("microseconds", FOUR_MICROSECONDS, "4 microseconds"),
    ("microseconds", FOUR_MILLISECONDS, "4 milliseconds"),
    ("microseconds", MICROSECONDS_101_943, "101 milliseconds"),
    ("microseconds", MILLISECONDS_1_337, "a second"),
    ("microseconds", 2, "2 seconds"),
    ("microseconds", 4, "4 seconds"),
    ("microseconds", ONE_HOUR + FOUR_MILLISECONDS, "an hour"),
    ("microseconds", ONE_DAY + FOUR_MILLISECONDS, "a day"),
    ("microseconds", ONE_YEAR + FOUR_MICROSECONDS, "a year"),
]


def test_naturaldelta_minimum_unit_sets_the_smallest_unit_shown():
    rule = spec(naturaldelta)
    for unit, s, text in MINIMUM_UNIT_ROWS:
        rule.if_(td(seconds=s), minimum_unit=unit).then_give(text)


def test_naturaldelta_minimum_unit_works_on_plain_seconds_too():
    rule = spec(naturaldelta)
    for unit, s, text in MINIMUM_UNIT_ROWS:
        rule.if_(s, minimum_unit=unit).then_give(text)


def test_naturaldelta_rejects_a_minimum_unit_it_cannot_honour():
    spec(naturaldelta).if_(1, minimum_unit="years").then_raise(
        ValueError, message="Minimum unit 'years' not supported"
    )


# ===== naturaltime ==========================================================


def test_naturaltime_past_moments_say_ago():
    rule = spec(naturaltime)
    rule.if_(td(0)).then_give("now")
    rule.if_(td(seconds=1)).then_give("a second ago")
    rule.if_(td(seconds=30)).then_give("30 seconds ago")
    rule.if_(td(minutes=1, seconds=29)).then_give("a minute ago")
    rule.if_(td(minutes=1, seconds=30)).then_give("2 minutes ago")
    rule.if_(td(minutes=2)).then_give("2 minutes ago")
    rule.if_(td(hours=1, minutes=29, seconds=30)).then_give("an hour ago")
    rule.if_(td(hours=1, minutes=30, seconds=30)).then_give("2 hours ago")
    rule.if_(td(hours=23, minutes=29, seconds=50)).then_give("23 hours ago")
    rule.if_(td(hours=23, minutes=50, seconds=50)).then_give("a day ago")
    rule.if_(td(days=1)).then_give("a day ago")
    rule.if_(td(days=500)).then_give("1 year, 4 months ago")
    rule.if_(td(days=365 + 4)).then_give("1 year, 4 days ago")
    rule.if_(td(days=365 + 35)).then_give("1 year, 1 month ago")
    rule.if_(td(days=365 * 2 + 35)).then_give("2 years ago")
    rule.if_(td(days=365 * 2 + 65)).then_give("2 years ago")
    rule.if_(22.5).then_give("22 seconds ago")
    rule.if_(23.5).then_give("24 seconds ago")
    rule.if_(23.9).then_give("24 seconds ago")
    rule.if_(30).then_give("30 seconds ago")


def test_naturaltime_future_moments_say_from_now():
    rule = spec(naturaltime)
    rule.if_(later(seconds=1), when=NOW).then_give("a second from now")
    rule.if_(later(seconds=30), when=NOW).then_give("30 seconds from now")
    rule.if_(later(minutes=1, seconds=29), when=NOW).then_give("a minute from now")
    rule.if_(later(minutes=1, seconds=30), when=NOW).then_give("2 minutes from now")
    rule.if_(later(minutes=2), when=NOW).then_give("2 minutes from now")
    rule.if_(later(hours=1, minutes=29, seconds=30), when=NOW).then_give("an hour from now")
    rule.if_(later(hours=1, minutes=30, seconds=30), when=NOW).then_give("2 hours from now")
    rule.if_(later(hours=23, minutes=29, seconds=50), when=NOW).then_give("23 hours from now")
    rule.if_(later(hours=23, minutes=50, seconds=50), when=NOW).then_give("a day from now")
    rule.if_(later(days=1), when=NOW).then_give("a day from now")
    rule.if_(later(days=500), when=NOW).then_give("1 year, 4 months from now")
    rule.if_(later(days=365 * 2 + 35), when=NOW).then_give("2 years from now")
    rule.if_(later(days=10000), when=NOW).then_give("27 years from now")


def test_naturaltime_a_negative_timedelta_is_in_the_future():
    rule = spec(naturaltime)
    rule.if_(td(days=-10000)).then_give("27 years from now")
    rule.if_(td(days=-800_000)).then_give("2,192 years from now")


def test_naturaltime_past_moments_given_as_datetimes():
    rule = spec(naturaltime)
    rule.if_(NOW - td(seconds=30), when=NOW).then_give("30 seconds ago")
    rule.if_(NOW - td(days=500), when=NOW).then_give("1 year, 4 months ago")
    rule.if_(NOW, when=NOW).then_give("now")


def test_naturaltime_far_future_datetime():
    rule = spec(naturaltime)
    rule.if_(dt.datetime(9999, 12, 31), when=NOW).then_give("7,995 years from now")


def test_naturaltime_timezone_aware_moments_compare_correctly():
    rule = spec(naturaltime)
    rule.if_(NOW_UTC, when=NOW_UTC).then_give("now")
    rule.if_(NOW_UTC - td(minutes=2), when=NOW_UTC).then_give("2 minutes ago")
    rule.if_(NOW_UTC - td(days=500), when=NOW_UTC).then_give("1 year, 4 months ago")
    rule.if_(NOW_UTC + td(minutes=2), when=NOW_UTC).then_give("2 minutes from now")
    rule.if_(NOW_UTC + td(days=10000), when=NOW_UTC).then_give("27 years from now")


@freeze_time("2010-02-02")
def test_naturaltime_defaults_to_the_current_time():
    rule = spec(naturaltime)
    rule.if_(NOW).then_give("now")
    rule.if_(NOW - td(seconds=30)).then_give("30 seconds ago")
    rule.if_(NOW + td(minutes=2)).then_give("2 minutes from now")
    rule.if_(NOW_UTC - td(hours=3)).then_give("3 hours ago")
    rule.if_(NOW_UTC + td(hours=3)).then_give("3 hours from now")


def test_naturaltime_without_months_counts_days_instead():
    rule = spec(naturaltime)
    rule.if_(td(seconds=30), months=False).then_give("30 seconds ago")
    rule.if_(td(days=17), months=False).then_give("17 days ago")
    rule.if_(td(days=47), months=False).then_give("47 days ago")
    rule.if_(td(days=500), months=False).then_give("1 year, 135 days ago")
    rule.if_(td(days=365 + 4), months=False).then_give("1 year, 4 days ago")
    rule.if_(td(days=365 + 35), months=False).then_give("1 year, 35 days ago")
    rule.if_(td(days=365 * 2 + 35), months=False).then_give("2 years ago")
    rule.if_(td(days=-10000), months=False).then_give("27 years from now")
    rule.if_(later(days=500), when=NOW, months=False).then_give("1 year, 135 days from now")


def test_naturaltime_leaves_non_numbers_alone():
    rule = spec(naturaltime)
    rule.if_("NaN").then_give("NaN")
    rule.if_(None).then_give("None")


def test_naturaltime_minimum_unit_defaults_to_seconds():
    rule = spec(naturaltime)
    rule.if_(td(seconds=ONE_MICROSECOND)).then_give("now")
    rule.if_(td(seconds=FOUR_MICROSECONDS)).then_give("now")
    rule.if_(td(seconds=ONE_MILLISECOND)).then_give("now")
    rule.if_(td(seconds=FOUR_MILLISECONDS)).then_give("now")
    rule.if_(td(seconds=2)).then_give("2 seconds ago")
    rule.if_(td(seconds=4)).then_give("4 seconds ago")
    rule.if_(td(seconds=ONE_HOUR + FOUR_MILLISECONDS)).then_give("an hour ago")
    rule.if_(td(seconds=ONE_DAY + FOUR_MILLISECONDS)).then_give("a day ago")
    rule.if_(td(seconds=ONE_YEAR + FOUR_MICROSECONDS)).then_give("a year ago")


def test_naturaltime_minimum_unit_sets_the_smallest_unit_shown():
    rule = spec(naturaltime)

    def ago(text):
        return "now" if text == "a moment" else text + " ago"

    for unit, s, text in MINIMUM_UNIT_ROWS:
        rule.if_(td(seconds=s), minimum_unit=unit).then_give(ago(text))


# ===== naturalday / naturaldate =============================================


class FakeDate:
    """Looks like a date but is out of range for datetime.date."""

    def __init__(self, year, month, day):
        self.year, self.month, self.day = year, month, day

    def __str__(self):
        return f"{self.year}-{self.month}-{self.day}"


VALUE_ERROR_DATE = FakeDate(290149024, 2, 2)
OVERFLOW_ERROR_DATE = FakeDate(120390192341, 2, 2)


@freeze_time("2010-02-02")
def test_naturalday_names_today_tomorrow_and_yesterday():
    rule = spec(naturalday)
    rule.if_(TODAY).then_give("today")
    rule.if_(TOMORROW).then_give("tomorrow")
    rule.if_(YESTERDAY).then_give("yesterday")


@freeze_time("2010-02-02")
def test_naturalday_other_days_use_the_month_and_day_or_your_format():
    rule = spec(naturalday)
    rule.if_(dt.date(2010, 3, 5)).then_give("Mar 05")
    rule.if_(dt.date(1982, 6, 27), "%Y.%m.%d").then_give("1982.06.27")


@freeze_time("2010-02-02")
def test_naturalday_leaves_things_that_are_not_dates_alone():
    rule = spec(naturalday)
    rule.if_("02/26/1984").then_give("02/26/1984")
    rule.if_(None).then_give("None")
    rule.if_("Not a date at all.").then_give("Not a date at all.")
    rule.if_(VALUE_ERROR_DATE).then_give(str(VALUE_ERROR_DATE))
    rule.if_(OVERFLOW_ERROR_DATE).then_give(str(OVERFLOW_ERROR_DATE))


@freeze_time("2010-02-02")
def test_naturaldate_names_today_tomorrow_and_yesterday():
    rule = spec(naturaldate)
    rule.if_(TODAY).then_give("today")
    rule.if_(TOMORROW).then_give("tomorrow")
    rule.if_(YESTERDAY).then_give("yesterday")


@freeze_time("2010-02-02")
def test_naturaldate_within_about_five_months_the_year_is_left_out():
    rule = spec(naturaldate)
    rule.if_(dt.date(2009, 10, 2)).then_give("Oct 02")
    rule.if_(dt.date(2009, 11, 2)).then_give("Nov 02")
    rule.if_(dt.date(2009, 12, 2)).then_give("Dec 02")
    rule.if_(dt.date(2010, 1, 2)).then_give("Jan 02")
    rule.if_(dt.date(2010, 3, 2)).then_give("Mar 02")
    rule.if_(dt.date(2010, 4, 2)).then_give("Apr 02")
    rule.if_(dt.date(2010, 5, 2)).then_give("May 02")
    rule.if_(dt.date(2010, 6, 2)).then_give("Jun 02")
    rule.if_(dt.date(2010, 7, 2)).then_give("Jul 02")
    rule.if_(dt.date(2010, 3, 5)).then_give("Mar 05")


@freeze_time("2010-02-02")
def test_naturaldate_further_away_the_year_is_included():
    rule = spec(naturaldate)
    rule.if_(dt.date(1982, 6, 27)).then_give("Jun 27 1982")
    rule.if_(dt.date(2009, 2, 2)).then_give("Feb 02 2009")
    rule.if_(dt.date(2009, 3, 2)).then_give("Mar 02 2009")
    rule.if_(dt.date(2009, 4, 2)).then_give("Apr 02 2009")
    rule.if_(dt.date(2009, 5, 2)).then_give("May 02 2009")
    rule.if_(dt.date(2009, 6, 2)).then_give("Jun 02 2009")
    rule.if_(dt.date(2009, 7, 2)).then_give("Jul 02 2009")
    rule.if_(dt.date(2009, 8, 2)).then_give("Aug 02 2009")
    rule.if_(dt.date(2009, 9, 2)).then_give("Sep 02 2009")
    rule.if_(dt.date(2010, 8, 2)).then_give("Aug 02 2010")
    rule.if_(dt.date(2010, 9, 2)).then_give("Sep 02 2010")
    rule.if_(dt.date(2010, 10, 2)).then_give("Oct 02 2010")
    rule.if_(dt.date(2010, 11, 2)).then_give("Nov 02 2010")
    rule.if_(dt.date(2010, 12, 2)).then_give("Dec 02 2010")
    rule.if_(dt.date(2011, 1, 2)).then_give("Jan 02 2011")
    rule.if_(dt.date(2011, 2, 2)).then_give("Feb 02 2011")


@freeze_time("2010-02-02")
def test_naturaldate_leaves_things_that_are_not_dates_alone():
    rule = spec(naturaldate)
    rule.if_(None).then_give("None")
    rule.if_("Not a date at all.").then_give("Not a date at all.")
    rule.if_(VALUE_ERROR_DATE).then_give(str(VALUE_ERROR_DATE))
    rule.if_(OVERFLOW_ERROR_DATE).then_give(str(OVERFLOW_ERROR_DATE))


@freeze_time("2023-10-15 23:00:00+00:00")
def test_naturaldate_compares_days_in_the_timezone_of_the_given_value():
    """The clock says Oct 15, 23:00 UTC. The same instant (Oct 16, 06:00 UTC) is a different 'day' per zone."""
    rule = spec(naturaldate)
    instant = dt.datetime(2023, 10, 16, hour=6, tzinfo=dt.timezone.utc)
    in_zone = lambda hours: instant.astimezone(dt.timezone(dt.timedelta(hours=hours)))
    rule.if_(instant).then_give("tomorrow")  # UTC: now is Oct 15, instant is Oct 16
    rule.if_(in_zone(11)).then_give("today")  # AEDT +11: both are Oct 16
    rule.if_(in_zone(2)).then_give("today")  # CEST +2: both are Oct 16
    rule.if_(in_zone(-4)).then_give("tomorrow")  # EDT -4: now Oct 15 19:00, instant Oct 16 02:00
    rule.if_(in_zone(-7)).then_give("today")  # PDT -7: both are Oct 15


# ===== precisedelta =========================================================


def test_precisedelta_a_single_unit_is_enough_when_nothing_else_is_left():
    rule = spec(precisedelta)
    rule.if_(td(microseconds=1), minimum_unit="microseconds").then_give("1 microsecond")
    rule.if_(td(microseconds=2), minimum_unit="microseconds").then_give("2 microseconds")
    rule.if_(td(microseconds=1000), minimum_unit="microseconds").then_give("1 millisecond")
    rule.if_(td(microseconds=2000), minimum_unit="microseconds").then_give("2 milliseconds")
    rule.if_(td(seconds=1), minimum_unit="seconds").then_give("1 second")
    rule.if_(1, minimum_unit="seconds").then_give("1 second")
    rule.if_(2, minimum_unit="seconds").then_give("2 seconds")
    rule.if_(60, minimum_unit="seconds").then_give("1 minute")
    rule.if_(120, minimum_unit="seconds").then_give("2 minutes")
    rule.if_(3600, minimum_unit="seconds").then_give("1 hour")
    rule.if_(3600 * 2, minimum_unit="seconds").then_give("2 hours")
    rule.if_(3600 * 24, minimum_unit="seconds").then_give("1 day")
    rule.if_(3600 * 24 * 2, minimum_unit="seconds").then_give("2 days")
    rule.if_(3600 * 24 * 365, minimum_unit="seconds").then_give("1 year")
    rule.if_(3600 * 24 * 365 * 2, minimum_unit="seconds").then_give("2 years")
    rule.if_(3600 * 24 * 365 * 1963, minimum_unit="seconds").then_give("1,963 years")


def test_precisedelta_lists_every_unit_that_is_present():
    rule = spec(precisedelta)
    rule.if_(td(microseconds=1001), minimum_unit="microseconds").then_give("1 millisecond and 1 microsecond")
    rule.if_(td(microseconds=2002), minimum_unit="microseconds").then_give(
        "2 milliseconds and 2 microseconds"
    )
    rule.if_(td(seconds=1, microseconds=2), minimum_unit="microseconds").then_give(
        "1 second and 2 microseconds"
    )
    rule.if_(td(hours=4, seconds=3, microseconds=2), minimum_unit="microseconds").then_give(
        "4 hours, 3 seconds and 2 microseconds"
    )
    rule.if_(td(days=5, hours=4, seconds=3, microseconds=2), minimum_unit="microseconds").then_give(
        "5 days, 4 hours, 3 seconds and 2 microseconds"
    )
    rule.if_(td(days=370, hours=4, seconds=3, microseconds=2), minimum_unit="microseconds").then_give(
        "1 year, 5 days, 4 hours, 3 seconds and 2 microseconds"
    )
    rule.if_(td(days=370, microseconds=2), minimum_unit="microseconds").then_give(
        "1 year, 5 days and 2 microseconds"
    )
    rule.if_(td(days=370, seconds=2), minimum_unit="microseconds").then_give("1 year, 5 days and 2 seconds")
    rule.if_(td(seconds=0.01), minimum_unit="minutes").then_give("0 minutes")
    rule.if_(td(days=-800000), minimum_unit="seconds").then_give("2,191 years, 9 months and 10 days")
    rule.if_(-90, minimum_unit="seconds").then_give("1 minute and 30 seconds")
    rule.if_(0, minimum_unit="seconds").then_give("0 seconds")
    rule.if_(td(days=1, hours=2), minimum_unit="seconds").then_give("1 day and 2 hours")


def test_precisedelta_months_are_30_and_a_half_days():
    rule = spec(precisedelta)
    rule.if_(td(days=31), minimum_unit="seconds").then_give("1 month")
    rule.if_(td(days=32), minimum_unit="seconds").then_give("1 month and 1 day")
    rule.if_(td(days=62), minimum_unit="seconds").then_give("2 months and 1 day")
    rule.if_(td(days=92), minimum_unit="seconds").then_give("3 months")
    rule.if_(td(days=31), minimum_unit="days").then_give("1 month")
    rule.if_(td(days=32), minimum_unit="days").then_give("1 month and 1 day")
    rule.if_(td(days=62), minimum_unit="days").then_give("2 months and 1 day")
    rule.if_(td(days=92), minimum_unit="days").then_give("3 months")


def test_precisedelta_format_controls_how_the_smallest_unit_is_rounded():
    rule = spec(precisedelta)
    rule.if_(td(microseconds=1001), minimum_unit="milliseconds", format="%0.4f").then_give(
        "1.0010 milliseconds"
    )
    rule.if_(td(microseconds=2002), minimum_unit="milliseconds", format="%0.4f").then_give(
        "2.0020 milliseconds"
    )
    rule.if_(td(microseconds=2002), minimum_unit="milliseconds", format="%0.2f").then_give("2 milliseconds")
    rule.if_(td(seconds=1, microseconds=230000), minimum_unit="seconds", format="%0.2f").then_give(
        "1.23 seconds"
    )
    rule.if_(td(hours=4, seconds=3, microseconds=200000), minimum_unit="seconds", format="%0.2f").then_give(
        "4 hours and 3.20 seconds"
    )
    rule.if_(td(days=5, hours=4, seconds=30 * 60), minimum_unit="seconds", format="%0.2f").then_give(
        "5 days, 4 hours and 30 minutes"
    )
    rule.if_(td(days=5, hours=4, seconds=30 * 60), minimum_unit="hours", format="%0.2f").then_give(
        "5 days and 4.50 hours"
    )
    rule.if_(td(days=5, hours=4, seconds=30 * 60), minimum_unit="days", format="%0.2f").then_give("5.19 days")
    rule.if_(td(days=120), minimum_unit="months", format="%0.2f").then_give("3.93 months")
    rule.if_(td(days=183), minimum_unit="years", format="%0.1f").then_give("0.5 years")
    rule.if_(0.01, minimum_unit="seconds", format="%0.3f").then_give("0.010 seconds")
    rule.if_(td(days=10, hours=6), minimum_unit="days", format="%0.2f").then_give("10.25 days")
    rule.if_(td(days=30.55), minimum_unit="days", format="%0.1f").then_give("30.6 days")


def test_precisedelta_a_month_is_30_and_a_half_days_but_the_remainder_rounds_down():
    rule = spec(precisedelta)
    rule.if_(td(days=31), minimum_unit="days", format="%d").then_give("1 month")
    rule.if_(td(days=31), minimum_unit="days", format="%.0f").then_give("1 month")
    rule.if_(td(days=32), minimum_unit="days", format="%d").then_give("1 month and 1 day")
    rule.if_(td(days=32), minimum_unit="days", format="%.0f").then_give("1 month and 1 day")
    rule.if_(td(days=62), minimum_unit="days", format="%d").then_give("2 months and 1 day")
    rule.if_(td(days=92), minimum_unit="days", format="%d").then_give("3 months")


def test_precisedelta_percent_d_truncates_while_percent_f_rounds():
    # 31 seconds is 0.52 minutes: %d truncates to 0, %.0f rounds to 1
    rule = spec(precisedelta)
    rule.if_(31, minimum_unit="minutes", format="%d").then_give("0 minutes")
    rule.if_(31, minimum_unit="minutes", format="%0.0f").then_give("1 minute")
    rule.if_(60 + 29.99, minimum_unit="minutes", format="%d").then_give("1 minute")
    rule.if_(60 + 29.99, minimum_unit="minutes", format="%.0f").then_give("1 minute")
    rule.if_(60 + 30, minimum_unit="minutes", format="%d").then_give("1 minute")
    rule.if_(60 + 30, minimum_unit="minutes", format="%.0f").then_give(
        "2 minutes"
    )  # a tie rounds away from zero
    rule.if_(60 * 60 + 30.99, minimum_unit="minutes", format="%.0f").then_give("1 hour")
    rule.if_(60 * 60 + 31, minimum_unit="minutes", format="%.0f").then_give("1 hour and 1 minute")
    rule.if_(9 * 60 * 60 - 1, minimum_unit="minutes", format="%0.0f").then_give("9 hours")
    rule.if_(td(days=30.99999), minimum_unit="minutes", format="%0.0f").then_give("1 month")
    rule.if_(td(minutes=59.5), minimum_unit="minutes", format="%0.0f").then_give("1 hour")


def test_precisedelta_rounding_up_carries_into_the_next_unit():
    rule = spec(precisedelta)
    rule.if_(td(microseconds=999.5), minimum_unit="microseconds", format="%0.0f").then_give("1 millisecond")
    rule.if_(td(milliseconds=999.5), minimum_unit="milliseconds", format="%0.0f").then_give("1 second")
    rule.if_(td(seconds=59.5), minimum_unit="seconds", format="%0.0f").then_give("1 minute")
    rule.if_(td(days=364), minimum_unit="months", format="%0.0f").then_give("1 year")
    rule.if_(91500, minimum_unit="hours", format="%0.0f").then_give("1 day and 1 hour")


def test_precisedelta_rounding_the_last_unit_can_land_on_a_tie():
    # 12.5 hours is a tie, so it rounds to the even number: 12
    rule = spec(precisedelta)
    rule.if_(td(days=30.5 * 3, minutes=30), minimum_unit="hours", format="%0.0f").then_give(
        "2 months, 30 days and 12 hours"
    )
    rule.if_(ONE_DAY - MILLISECONDS_1_337, minimum_unit="seconds", format="%.1f").then_give(
        "23 hours, 59 minutes and 58.7 seconds"
    )
    rule.if_(ONE_DAY - ONE_MILLISECOND, minimum_unit="seconds", format="%.4f").then_give(
        "23 hours, 59 minutes and 59.9990 seconds"
    )


def test_precisedelta_suppress_folds_a_unit_into_the_next_smaller_one():
    rule = spec(precisedelta)
    micro = "microseconds"
    rule.if_(td(microseconds=1200), minimum_unit=micro, suppress=[]).then_give(
        "1 millisecond and 200 microseconds"
    )
    rule.if_(td(microseconds=1200), minimum_unit=micro, suppress=["milliseconds"]).then_give(
        "1200 microseconds"
    )
    rule.if_(td(microseconds=1200), minimum_unit=micro, suppress=["microseconds"]).then_give(
        "1.20 milliseconds"
    )
    rule.if_(td(seconds=1, microseconds=200), minimum_unit=micro, suppress=["seconds"]).then_give(
        "1000 milliseconds and 200 microseconds"
    )
    rule.if_(td(seconds=1, microseconds=200000), minimum_unit=micro, suppress=["milliseconds"]).then_give(
        "1 second and 200000 microseconds"
    )
    rule.if_(
        td(seconds=1, microseconds=200000),
        minimum_unit=micro,
        suppress=["milliseconds", "microseconds"],
    ).then_give("1.20 seconds")
    rule.if_(
        td(hours=4, seconds=30, microseconds=200), minimum_unit=micro, suppress=["microseconds"]
    ).then_give("4 hours, 30 seconds and 0.20 milliseconds")
    rule.if_(td(hours=4, seconds=30, microseconds=200), minimum_unit=micro, suppress=["seconds"]).then_give(
        "4 hours, 30000 milliseconds and 200 microseconds"
    )
    rule.if_(
        td(hours=4, seconds=30, microseconds=200),
        minimum_unit=micro,
        suppress=["seconds", "milliseconds"],
    ).then_give("4 hours and 30000200 microseconds")
    rule.if_(td(hours=4, seconds=30, microseconds=200), minimum_unit=micro, suppress=["hours"]).then_give(
        "240 minutes, 30 seconds and 200 microseconds"
    )
    rule.if_(
        td(hours=4, seconds=30, microseconds=200),
        minimum_unit=micro,
        suppress=["hours", "seconds", "milliseconds", "microseconds"],
    ).then_give("240.50 minutes")


def test_precisedelta_leaves_non_numbers_alone():
    spec(precisedelta).if_(None).then_give("None")


def test_precisedelta_cannot_suppress_the_only_unit_it_may_show():
    spec(precisedelta).if_(1, minimum_unit="years", suppress=["years"]).then_raise(
        ValueError, message="Minimum unit is suppressed and no suitable replacement was found"
    )


# ===== internals ============================================================


def test_time_units_are_ordered_from_small_to_large():
    years, minutes = time.Unit["YEARS"], time.Unit["MINUTES"]
    expect(minutes < years, "MINUTES < YEARS").should.be.true()
    expect(years > minutes, "YEARS > MINUTES").should.be.true()
    spec(lambda: years < "foo").if_().then_raise(TypeError)


def test_rounding_by_format_follows_the_format():
    rule = spec(time._rounding_by_fmt)
    rule.if_("%.2f", 1.011).then_give(1.01)
    rule.if_("%.0f", 1.01).then_give(1.0)
    rule.if_("%.0f", 1.5).then_give(2.0)
    rule.if_("%10.0f", 1.01).then_give(1.0)
    rule.if_("%i", 1.01).then_give(1)
    # %d is surprising: it truncates... until the float is too close to the next integer
    rule.if_("%d", 1.999999999999999).then_give(1)
    rule.if_("%d", 1.9999999999999999).then_give(2)
