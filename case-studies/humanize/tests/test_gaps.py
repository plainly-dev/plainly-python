"""New tests: behaviour the upstream suite never pinned down.

Found by (1) reading each docstring and function for unspecified boundaries, and
(2) mutation checking the upstream suite: changing `delta.microseconds < 1000` to `< 999`
in humanize/time.py did not fail a single upstream test.
"""

import datetime as dt

from humanize import intword, naturaldelta, naturalsize, precisedelta

from plainly import spec

td = dt.timedelta


def test_naturaldelta_just_under_a_millisecond_stays_in_microseconds():
    rule = spec(naturaldelta)
    rule.if_(td(microseconds=999), minimum_unit="microseconds").then_give("999 microseconds")
    rule.if_(td(microseconds=1000), minimum_unit="microseconds").then_give("1 millisecond")
    rule.if_(td(microseconds=1999), minimum_unit="microseconds").then_give("1 millisecond")


def test_naturalsize_switches_unit_exactly_at_the_base():
    rule = spec(naturalsize)
    rule.if_(999).then_give("999 Bytes")
    rule.if_(1000).then_give("1.0 kB")
    rule.if_(1000, binary=True).then_give("1000 Bytes")
    rule.if_(1023, binary=True).then_give("1023 Bytes")
    rule.if_(1024, binary=True).then_give("1.0 KiB")
    rule.if_(-0.5).then_give("0 Bytes")


def test_intword_negative_values_roll_over_like_positive_ones():
    rule = spec(intword)
    rule.if_(-999999).then_give("-1.0 million")
    rule.if_(-1000).then_give("-1.0 thousand")
    rule.if_(1500, "%.0f").then_give("2 thousand")


def test_precisedelta_with_a_coarse_minimum_unit_drops_the_remainder():
    rule = spec(precisedelta)
    rule.if_(td(days=1), minimum_unit="hours").then_give("1 day")


def test_an_unknown_minimum_unit_is_rejected():
    # The error is a bare KeyError('BOGUS'); a ValueError naming the allowed units would be kinder.
    spec(naturaldelta).if_(1, minimum_unit="bogus").then_raise(KeyError)
    spec(precisedelta).if_(td(days=1), minimum_unit="bogus").then_raise(KeyError)


def test_naturalsize_non_finite_floats_are_inconsistent_with_the_rest_of_the_library():
    """Documents CURRENT behaviour, likely worth a maintainer's look: every number formatter
    returns "NaN" / "+Inf" for these, but naturalsize raises (NaN) or prints "inf QB" (infinity)."""
    spec(naturalsize).if_(float("nan")).then_raise(ValueError, message="cannot convert float NaN")
    spec(naturalsize).if_(float("inf")).then_give("inf QB")
