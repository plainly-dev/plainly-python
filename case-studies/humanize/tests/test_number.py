"""humanize number functions, rewritten with plainly.

Run `pytest --plainly` to read this file as a list of sentences.
"""

import math

import humanize
from humanize import apnumber, clamp, fractional, intcomma, intword, metric, ordinal, scientific

from plainly import compact, expect, spec


def spells_out_non_finite_numbers(func):
    """Every number formatter shares one rule for NaN and infinity."""
    rule = spec(func)
    rule.if_(math.nan).then_give("NaN")
    rule.if_(math.inf).then_give("+Inf")
    rule.if_(-math.inf).then_give("-Inf")
    rule.if_("nan").then_give("NaN")
    rule.if_("-inf").then_give("-Inf")


# ----- ordinal -------------------------------------------------------------


def test_ordinal_picks_st_nd_rd_th():
    rule = spec(ordinal)
    rule.if_("1").then_give("1st")
    rule.if_("2").then_give("2nd")
    rule.if_("3").then_give("3rd")
    rule.if_("4").then_give("4th")
    rule.if_(21).then_give("21st")
    rule.if_(22).then_give("22nd")
    rule.if_(23).then_give("23rd")
    rule.if_(101).then_give("101st")
    rule.if_(102).then_give("102nd")
    rule.if_(103).then_give("103rd")


def test_ordinal_teens_always_take_th():
    rule = spec(ordinal)
    rule.if_("11").then_give("11th")
    rule.if_("12").then_give("12th")
    rule.if_("13").then_give("13th")
    rule.if_("111").then_give("111th")
    rule.if_(112).then_give("112th")


def test_ordinal_leaves_non_numbers_alone():
    rule = spec(ordinal)
    rule.if_("something else").then_give("something else")
    rule.if_(None).then_give("None")


def test_ordinal_non_finite():
    spells_out_non_finite_numbers(ordinal)


def test_ordinal_edge_values():
    # Documents current behaviour; a negative ordinal is arguably meaningless.
    rule = spec(ordinal)
    rule.if_(0).then_give("0th")
    rule.if_(-1).then_give("-1th")
    rule.if_(1.5).then_give("1st")
    rule.if_(1, "female").then_give("1st")


# ----- intcomma ------------------------------------------------------------


def test_intcomma_groups_thousands():
    rule = spec(intcomma)
    rule.if_(0).then_give("0")
    rule.if_(100).then_give("100")
    rule.if_(999).then_give("999")
    rule.if_(1000).then_give("1,000")
    rule.if_(10123).then_give("10,123")
    rule.if_(10311).then_give("10,311")
    rule.if_(1_000_000).then_give("1,000,000")
    rule.if_(-1234567).then_give("-1,234,567")


def test_intcomma_accepts_numbers_as_text():
    rule = spec(intcomma)
    rule.if_("100").then_give("100")
    rule.if_("1000").then_give("1,000")
    rule.if_("10123").then_give("10,123")
    rule.if_("10311").then_give("10,311")
    rule.if_("1000000").then_give("1,000,000")


def test_intcomma_keeps_decimals_when_not_told_otherwise():
    rule = spec(intcomma)
    rule.if_(1_234_567.25).then_give("1,234,567.25")
    rule.if_("1234567.1234567").then_give("1,234,567.1234567")
    rule.if_(14308.40).then_give("14,308.4")
    rule.if_(1234.5454545).then_give("1,234.5454545")
    rule.if_(14308.40, None).then_give("14,308.4")
    rule.if_(1234.5454545, None).then_give("1,234.5454545")


def test_intcomma_rounds_to_the_requested_decimal_places():
    rule = spec(intcomma)
    rule.if_("1234567.1234567", 0).then_give("1,234,567")
    rule.if_("1234567.1234567", 1).then_give("1,234,567.1")
    rule.if_("1234567.1234567", 10).then_give("1,234,567.1234567000")
    rule.if_("1234567", 1).then_give("1,234,567.0")
    rule.if_(14308.40, 1).then_give("14,308.4")
    rule.if_(14308.40, 2).then_give("14,308.40")
    rule.if_(14308.40, 3).then_give("14,308.400")
    rule.if_(1234.5454545, 0).then_give("1,235")
    rule.if_(1234.5454545, 1).then_give("1,234.5")
    rule.if_(1234.5454545, 2).then_give("1,234.55")
    rule.if_(1234.5454545, 3).then_give("1,234.545")
    rule.if_(1234.5454545, 10).then_give("1,234.5454545000")


def test_intcomma_does_not_lose_precision_on_huge_integers():
    for sign, prefix in [(1, ""), (-1, "-")]:
        value = sign * (10**400 + 123)
        expected = prefix + "10" + ",000" * 132 + ",123"
        expect(intcomma(value), f"intcomma({prefix}(10**400 + 123))", show=compact).should.be(expected)


def test_intcomma_leaves_non_numbers_alone():
    rule = spec(intcomma)
    rule.if_(None).then_give("None")
    rule.if_("abc").then_give("abc")


def test_intcomma_non_finite():
    spells_out_non_finite_numbers(intcomma)


# ----- intword -------------------------------------------------------------


def test_intword_below_a_thousand_is_just_the_number():
    rule = spec(intword)
    rule.if_("0").then_give("0")
    rule.if_("100").then_give("100")
    rule.if_("-100").then_give("-100")
    rule.if_(999).then_give("999")


def test_intword_names_the_magnitude():
    rule = spec(intword)
    rule.if_("1000").then_give("1.0 thousand")
    rule.if_("12400").then_give("12.4 thousand")
    rule.if_("12490").then_give("12.5 thousand")
    rule.if_("1000000").then_give("1.0 million")
    rule.if_("-1000000").then_give("-1.0 million")
    rule.if_("1200000").then_give("1.2 million")
    rule.if_("1290000").then_give("1.3 million")
    rule.if_("1000000000").then_give("1.0 billion")
    rule.if_("-1000000000").then_give("-1.0 billion")
    rule.if_("2000000000").then_give("2.0 billion")
    rule.if_("1000000000000").then_give("1.0 trillion")
    rule.if_("6000000000000").then_give("6.0 trillion")
    rule.if_("-6000000000000").then_give("-6.0 trillion")
    rule.if_("1000000000000000").then_give("1.0 quadrillion")
    rule.if_("1300000000000000").then_give("1.3 quadrillion")
    rule.if_("-1300000000000000").then_give("-1.3 quadrillion")
    rule.if_("3500000000000000000000").then_give("3.5 sextillion")
    rule.if_("8100000000000000000000000000000000").then_give("8.1 decillion")
    rule.if_("-8100000000000000000000000000000000").then_give("-8.1 decillion")


def test_intword_rounds_up_into_the_next_name():
    rule = spec(intword)
    rule.if_("999999999").then_give("1.0 billion")
    rule.if_("999999999999").then_give("1.0 trillion")
    rule.if_("999999999999999").then_give("1.0 quadrillion")


def test_intword_between_decillion_and_googol_there_is_no_name():
    rule = spec(intword)
    rule.if_(10**36).then_give("1000.0 decillion")
    rule.if_(1_100_000_000_000_000_000_000_000_000_000_000_000).then_give("1100.0 decillion")
    rule.if_(2_100_000_000_000_000_000_000_000_000_000_000_000).then_give("2100.0 decillion")


def test_intword_googol():
    rule = spec(intword, show=compact)
    rule.if_(2e100).then_give("2.0 googol")
    rule.if_(10**100).then_give("1.0 googol")
    rule.if_(10**101).then_give("10.0 googol")


def test_intword_accepts_a_format():
    rule = spec(intword)
    rule.if_("1230000", "%0.2f").then_give("1.23 million")
    rule.if_("1234567", "%.0f").then_give("1 million")
    rule.if_("1234567", "%.1f").then_give("1.2 million")
    rule.if_("1234567", "%.2f").then_give("1.23 million")
    rule.if_("1234567", "%.3f").then_give("1.235 million")
    rule.if_("999500", "%.0f").then_give("1 million")
    rule.if_("999499", "%.0f").then_give("999 thousand")
    rule.if_(1000, "%d").then_give("1 thousand")


def test_intword_leaves_non_numbers_alone():
    rule = spec(intword)
    rule.if_(None).then_give("None")
    rule.if_("abc").then_give("abc")


def test_intword_non_finite():
    spells_out_non_finite_numbers(intword)


def test_intword_has_a_human_name_for_every_power():
    expect(len(humanize.number.powers), "number of powers").should.be(len(humanize.number.human_powers))


def test_intword_rounding_up_never_leaves_1000_of_the_smaller_unit():
    """Regression: 10**24 - 1 once read '1000.0 sextillion' instead of '1.0 septillion'."""
    names = [
        "million",
        "billion",
        "trillion",
        "quadrillion",
        "quintillion",
        "sextillion",
        "septillion",
        "octillion",
        "nonillion",
        "decillion",
    ]
    for name, exponent in zip(names, range(6, 34, 3)):
        just_below = 10**exponent - 1
        expect(intword(just_below), f"intword(10**{exponent} - 1)").should.be(f"1.0 {name}")
        expect(intword(just_below, "%.0f"), f"intword(10**{exponent} - 1, '%.0f')").should.be(f"1 {name}")


# ----- apnumber ------------------------------------------------------------


def test_apnumber_spells_out_zero_to_nine():
    rule = spec(apnumber)
    rule.if_(0).then_give("zero")
    rule.if_(1).then_give("one")
    rule.if_(2).then_give("two")
    rule.if_(4).then_give("four")
    rule.if_(5).then_give("five")
    rule.if_(9).then_give("nine")
    rule.if_("7").then_give("seven")
    rule.if_(9.5).then_give("nine")


def test_apnumber_uses_digits_from_ten_up_and_for_negatives():
    rule = spec(apnumber)
    rule.if_(10).then_give("10")
    rule.if_(-1).then_give("-1")


def test_apnumber_leaves_non_numbers_alone():
    rule = spec(apnumber)
    rule.if_(None).then_give("None")
    rule.if_("abc").then_give("abc")


def test_apnumber_non_finite():
    spells_out_non_finite_numbers(apnumber)


# ----- fractional ----------------------------------------------------------


def test_fractional_writes_mixed_numbers():
    rule = spec(fractional)
    rule.if_(1).then_give("1")
    rule.if_(2.0).then_give("2")
    rule.if_(4.0 / 3.0).then_give("1 1/3")
    rule.if_(5.0 / 6.0).then_give("5/6")
    rule.if_("7").then_give("7")
    rule.if_("8.9").then_give("8 9/10")
    rule.if_(1 / 3).then_give("1/3")
    rule.if_(1.5).then_give("1 1/2")
    rule.if_(0.3).then_give("3/10")
    rule.if_(0.333).then_give("333/1000")


def test_fractional_handles_zero_and_negatives():
    rule = spec(fractional)
    rule.if_(0).then_give("0")
    rule.if_(0.0).then_give("0")
    rule.if_(-1.3).then_give("-1 3/10")
    rule.if_(-2.5).then_give("-2 1/2")
    rule.if_(-0.5).then_give("-1/2")


def test_fractional_rounds_values_that_are_almost_whole():
    rule = spec(fractional)
    rule.if_(2.9999999).then_give("3")
    rule.if_(0.9999999).then_give("1")
    rule.if_(-2.9999999).then_give("-3")


def test_fractional_leaves_non_numbers_alone():
    rule = spec(fractional)
    rule.if_("ten").then_give("ten")
    rule.if_(None).then_give("None")
    rule.if_("1/3").then_give("1/3")


def test_fractional_non_finite():
    spells_out_non_finite_numbers(fractional)


# ----- scientific ----------------------------------------------------------


def test_scientific_writes_powers_of_ten_with_two_decimals():
    rule = spec(scientific)
    rule.if_(1000).then_give("1.00 x 10³")
    rule.if_(-1000).then_give("-1.00 x 10³")
    rule.if_(5.5).then_give("5.50 x 10⁰")
    rule.if_(5781651000).then_give("5.78 x 10⁹")
    rule.if_("1000").then_give("1.00 x 10³")
    rule.if_("99").then_give("9.90 x 10¹")
    rule.if_(0).then_give("0.00 x 10⁰")
    rule.if_(0.3).then_give("3.00 x 10⁻¹")


def test_scientific_handles_very_large_and_very_small_exponents():
    rule = spec(scientific)
    rule.if_(1e20).then_give("1.00 x 10²⁰")
    rule.if_(2e-20).then_give("2.00 x 10⁻²⁰")
    rule.if_(-3e20).then_give("-3.00 x 10²⁰")
    rule.if_(-4e-20).then_give("-4.00 x 10⁻²⁰")


def test_scientific_accepts_a_number_of_decimals():
    rule = spec(scientific)
    rule.if_(1000, 1).then_give("1.0 x 10³")
    rule.if_(0.3, 1).then_give("3.0 x 10⁻¹")
    rule.if_(1000, 0).then_give("1 x 10³")
    rule.if_(0.3, 0).then_give("3 x 10⁻¹")


def test_scientific_leaves_non_numbers_alone():
    rule = spec(scientific)
    rule.if_("foo").then_give("foo")
    rule.if_(None).then_give("None")
    rule.if_("abc", 2).then_give("abc")


def test_scientific_non_finite():
    spells_out_non_finite_numbers(scientific)


# ----- clamp ---------------------------------------------------------------


def test_clamp_formats_values_inside_the_limits_normally():
    rule = spec(clamp)
    rule.if_(1).then_give("1")
    rule.if_(0.0001, "{:.0%}").then_give("0%")
    rule.if_(0.5, "{:.0%}", 1).then_give("<100%")


def test_clamp_marks_values_below_the_floor():
    rule = spec(clamp)
    rule.if_(0.0001, "{:.0%}", 0.01).then_give("<1%")
    rule.if_(0.0001, "{:.0%}", 0.01, None, "under ", None).then_give("under 1%")
    rule.if_(1, humanize.intword, 1e6, None, "under ").then_give("under 1.0 million")
    rule.if_(5, floor=10).then_give("<10")


def test_clamp_marks_values_above_the_ceiling():
    rule = spec(clamp)
    rule.if_(0.9999, "{:.0%}", None, 0.99).then_give(">99%")
    rule.if_(0.9999, "{:.0%}", None, 0.99, None, "above ").then_give("above 99%")
    rule.if_(5, ceil=3).then_give(">3")


def test_clamp_leaves_missing_values_alone():
    rule = spec(clamp)
    rule.if_(None).then_give(None)


def test_clamp_non_finite():
    rule = spec(clamp)
    rule.if_(math.nan).then_give("NaN")
    rule.if_(math.inf).then_give("+Inf")
    rule.if_(-math.inf).then_give("-Inf")


def test_clamp_rejects_a_format_that_is_neither_text_nor_a_function():
    spec(clamp).if_(5, format=3).then_raise(ValueError, message="Invalid format")


# ----- metric --------------------------------------------------------------


def test_metric_uses_three_significant_figures_by_default():
    rule = spec(metric)
    rule.if_(0).then_give("0.00")
    rule.if_(0.0).then_give("0.00")
    rule.if_(1.23456).then_give("1.23")
    rule.if_(12.3456).then_give("12.3")
    rule.if_(123.456).then_give("123")
    rule.if_(100).then_give("100")
    rule.if_(-1500, "V").then_give("-1.50 kV")


def test_metric_adds_a_unit_after_the_prefix():
    rule = spec(metric)
    rule.if_(1, "Hz").then_give("1.00 Hz")
    rule.if_(1.0, "W").then_give("1.00 W")
    rule.if_(3, "C").then_give("3.00 C")
    rule.if_(1, "°").then_give("1.00°")
    rule.if_(0.1, "°").then_give("100m°")


def test_metric_big_numbers_get_kilo_mega_and_beyond():
    rule = spec(metric)
    rule.if_(1234.56).then_give("1.23 k")
    rule.if_(200_000).then_give("200 k")
    rule.if_(1e25, "m").then_give("10.0 Ym")
    rule.if_(1e26, "m").then_give("100 Ym")
    rule.if_(1e27, "A").then_give("1.00 RA")
    rule.if_(1.234e28, "A").then_give("12.3 RA")
    rule.if_(1.235e29, "A").then_give("124 RA")
    rule.if_(2.596e32, "F").then_give("260 QF")


def test_metric_small_numbers_get_milli_micro_and_beyond():
    rule = spec(metric)
    rule.if_(0.12).then_give("120 m")
    rule.if_(0.012).then_give("12.0 m")
    rule.if_(0.0012).then_give("1.20 m")
    rule.if_(0.1).then_give("100 m")
    rule.if_(0.00012).then_give("120 μ")
    rule.if_(1e-23).then_give("10.0 y")
    rule.if_(1e-24).then_give("1.00 y")
    rule.if_(1e-25).then_give("100 r")
    rule.if_(1e-26).then_give("10.0 r")
    rule.if_(1.234e-28, "A").then_give("123 qA")
    rule.if_(2.56e-30, "V").then_give("2.56 qV")


def test_metric_beyond_the_largest_prefix_falls_back_to_scientific():
    rule = spec(metric)
    rule.if_(1e50).then_give("1.00 x 10⁵⁰")
    rule.if_(1e-50).then_give("1.00 x 10⁻⁵⁰")


def test_metric_rounding_up_moves_to_the_next_prefix_without_an_extra_digit():
    rule = spec(metric)
    rule.if_(9999).then_give("10.0 k")
    rule.if_(99999).then_give("100 k")
    rule.if_(9.99999).then_give("10.0")
    rule.if_(-9999).then_give("-10.0 k")
    rule.if_(9.999, "", 2).then_give("10")
    rule.if_(999.4).then_give("999")
    rule.if_(999.9, "V").then_give("1.00 kV")
    rule.if_(999.99, "V").then_give("1.00 kV")
    rule.if_(999_999, "V").then_give("1.00 MV")
    rule.if_(0.0009999, "V").then_give("1.00 mV")


def test_metric_precision_sets_the_significant_figures():
    rule = spec(metric)
    rule.if_(3, "W", 5).then_give("3.0000 W")
    rule.if_(12345, "", 6).then_give("12.3450 k")
    rule.if_(1.5123, "", 0).then_give("2")
    rule.if_(10.5123, "", 0).then_give("11")
    rule.if_(10.5123, "", 1).then_give("11")
    rule.if_(10.5123, "", 2).then_give("11")
    rule.if_(10.5123, "", 3).then_give("10.5")
    rule.if_(1, "", 0).then_give("1")
    rule.if_(10, "", 0).then_give("10")
    rule.if_(100, "", 0).then_give("100")
    rule.if_(1000, "", 0).then_give("1 k")
    rule.if_(1, "", 1).then_give("1")
    rule.if_(10, "", 1).then_give("10")
    rule.if_(100, "", 1).then_give("100")
    rule.if_(1000, "", 1).then_give("1 k")
    rule.if_(1, "", 2).then_give("1.0")
    rule.if_(10, "", 2).then_give("10")
    rule.if_(100, "", 2).then_give("100")
    rule.if_(1000, "", 2).then_give("1.0 k")
    rule.if_(1, "", 3).then_give("1.00")
    rule.if_(10, "", 3).then_give("10.0")
    rule.if_(100, "", 3).then_give("100")
    rule.if_(1000, "", 3).then_give("1.00 k")


def test_metric_non_finite():
    rule = spec(metric)
    rule.if_(math.nan).then_give("NaN")
    rule.if_(math.nan, "m").then_give("NaN")
    rule.if_(math.inf).then_give("+Inf")
    rule.if_(-math.inf).then_give("-Inf")
