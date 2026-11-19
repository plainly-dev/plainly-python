"""semver comparison, rewritten with plainly.

Left out on purpose: the DeprecationWarning checks for `Version == "1.0.0"` and `Version == (1, 0, 0)`.
"""

import semver
from semver import Version

from plainly import compact, expect, spec

from rules import (
    is_different,
    is_equal,
    is_greater_or_equal,
    is_greater_than,
    is_less_or_equal,
    is_less_than,
    parse,
    sorted_versions,
)

compare = spec(semver.compare, show=compact)
compare_to = spec(lambda a, b: Version.parse(a).compare(b), says="{} compared with {}", show=compact)
compare_prereleases = spec(
    lambda a, b: Version(0, 0, 0, prerelease=a).compare(Version(0, 0, 0, prerelease=b)),
    says="prerelease {} compared with prerelease {}",
)
TEN_THOUSAND_DIGITS = "1" * 5000


def test_compare_gives_minus_one_when_the_first_is_older():
    compare.if_("1.0.0", "2.0.0").then_give(-1)
    compare.if_("1.0.0-alpha", "1.0.0-alpha.1").then_give(-1)
    compare.if_("1.0.0-alpha.1", "1.0.0-alpha.beta").then_give(-1)
    compare.if_("1.0.0-alpha.beta", "1.0.0-beta").then_give(-1)
    compare.if_("1.0.0-beta", "1.0.0-beta.2").then_give(-1)
    compare.if_("1.0.0-beta.2", "1.0.0-beta.11").then_give(-1)
    compare.if_("1.0.0-beta.11", "1.0.0-rc.1").then_give(-1)
    compare.if_("1.0.0-rc.1", "1.0.0").then_give(-1)


def test_compare_gives_plus_one_when_the_first_is_newer():
    compare.if_("2.0.0", "1.0.0").then_give(1)
    compare.if_("1.0.0-alpha.1", "1.0.0-alpha").then_give(1)
    compare.if_("1.0.0-alpha.beta", "1.0.0-alpha.1").then_give(1)
    compare.if_("1.0.0-beta", "1.0.0-alpha.beta").then_give(1)
    compare.if_("1.0.0-beta.2", "1.0.0-beta").then_give(1)
    compare.if_("1.0.0-beta.11", "1.0.0-beta.2").then_give(1)
    compare.if_("1.0.0-rc.1", "1.0.0-beta.11").then_give(1)
    compare.if_("1.0.0", "1.0.0-rc.1").then_give(1)
    compare.if_("1.0.0-rc1", "1.0.0-rc0").then_give(1)


def test_compare_gives_zero_for_equal_versions():
    compare.if_("2.0.0", "2.0.0").then_give(0)
    compare.if_("1.1.9-rc.1", "1.1.9-rc.1").then_give(0)
    compare.if_("1.1.9+build.1", "1.1.9+build.1").then_give(0)
    compare.if_("1.1.9-rc.1+build.1", "1.1.9-rc.1+build.1").then_give(0)


def test_the_build_is_ignored_when_comparing():
    compare.if_("1.0.0+build.1", "1.0.0").then_give(0)
    compare.if_("1.0.0-alpha.1+build.1", "1.0.0-alpha.1").then_give(0)
    compare.if_("1.0.0+build.1", "1.0.0-alpha.1").then_give(1)
    compare.if_("1.0.0+build.1", "1.0.0-alpha.1+build.1").then_give(1)
    compare.if_("1.1.9-rc.1", "1.1.9-rc.1+build.1").then_give(0)
    compare.if_("1.1.9-rc.1", "1.1.9+build.1").then_give(-1)
    compare.if_("1.0.0-rc.1+build.1", "1.0.0").then_give(-1)


def test_a_prerelease_with_letters_is_older_than_the_release_with_a_build():
    compare.if_("1.9.1-1unms", "1.9.1+1").then_give(-1)


def test_the_specification_chain_is_ordered_in_both_directions():
    chain = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.3.7+build",
    ]
    for older, newer in zip(chain, chain[1:]):
        compare.if_(older, newer).then_give(-1)
        compare.if_(newer, older).then_give(1)


def test_compare_rejects_text_that_is_not_a_version():
    compare.if_("foo", "bar").then_raise(ValueError)
    compare.if_("1.0", "1.0.0").then_raise(ValueError)
    compare.if_("1.x", "1.0.0").then_raise(ValueError)


def test_compare_rejects_things_that_are_not_versions_at_all():
    compare.if_(1).then_raise(TypeError)
    spec(lambda: Version(3, 4, 5).compare(4), name="compare a version with 4").if_().then_raise(TypeError)
    for other in [1, 1.0, 1.23, 1 + 5j]:
        compare_to.if_("1.0.0", other).then_raise(TypeError)


def test_a_version_can_be_compared_with_a_tuple_a_list_or_a_dictionary():
    compare_to.if_("1.0.0", (1, 0, 0)).then_give(0)
    compare_to.if_("1.0.0", [1, 0, 0]).then_give(0)
    compare_to.if_("1.0.0", {"major": 1, "minor": 0, "patch": 0}).then_give(0)


def test_less_than():
    is_less_than.if_("1.0.0", "2.0.0").then_give(True)
    is_less_than.if_("0.10.4", "0.10.5").then_give(True)
    is_less_than.if_("0.10.4", "0.10.4").then_give(False)
    is_less_than.if_("0.10.4", "0.10.4-beta.1").then_give(False)


def test_less_or_equal():
    is_less_or_equal.if_("0.10.4", "0.10.5").then_give(True)
    is_less_or_equal.if_("0.10.4", "0.10.4").then_give(True)
    is_less_or_equal.if_("0.10.4", "0.10.4-beta.1").then_give(False)


def test_greater_than():
    is_greater_than.if_("0.10.4", "0.10.4-beta.1").then_give(True)
    is_greater_than.if_("0.10.4", "0.10.4").then_give(False)
    is_greater_than.if_("0.10.4", "0.10.5").then_give(False)


def test_greater_or_equal():
    is_greater_or_equal.if_("0.10.4", "0.10.4-beta.1").then_give(True)
    is_greater_or_equal.if_("0.10.4", "0.10.4").then_give(True)
    is_greater_or_equal.if_("0.10.4", "0.10.5").then_give(False)


def test_equal_and_different():
    is_equal.if_("0.10.4", "0.10.4").then_give(True)
    is_equal.if_("0.10.4", "0.10.4-beta.1").then_give(False)
    is_equal.if_("0.10.4", "0.10.5").then_give(False)
    is_different.if_("0.10.4", "0.10.4-beta.1").then_give(True)
    is_different.if_("0.10.4", "0.10.5").then_give(True)
    is_different.if_("0.10.4", "0.10.4").then_give(False)


def test_numbers_are_compared_as_numbers_not_as_text():
    is_less_than.if_("1.9.1", "1.10.0").then_give(True)
    expect(Version("2") < Version(10), "Version('2') < Version(10)").should.be.true()
    expect(Version("2") < Version("10"), "Version('2') < Version('10')").should.be.true()


def test_prerelease_and_build_may_be_given_as_numbers():
    expect(
        Version(1, 9, 1, 1, 1) < Version(1, 9, 1, 2, 1), "Version(1, 9, 1, 1, 1) < Version(1, 9, 1, 2, 1)"
    ).should.be.true()


def test_very_long_numeric_prereleases_are_ordered_correctly():
    long_version = "0.0.0-" + TEN_THOUSAND_DIGITS
    compare.if_(long_version, "0.0.0-2").then_give(1)
    compare.if_("0.0.0-2", long_version).then_give(-1)
    compare_to.if_(long_version, long_version).then_give(0)
    is_less_than.if_(long_version, "0.0.0").then_give(True)
    sorted_versions.if_("0.0.0-" + "1" + "0" * 4999, "0.0.0-" + "9" * 4999).then_give(
        ["0.0.0-" + "9" * 4999, "0.0.0-" + "1" + "0" * 4999]
    )
    sorted_versions.if_("0.0.0-alpha", "0.0.0-" + "1" * 5000).then_give(
        ["0.0.0-" + "1" * 5000, "0.0.0-alpha"]
    )


def test_long_prereleases_with_a_text_prefix_are_ordered_by_length_when_the_start_matches():
    short, long = "0.0.0-alpha." + "1" * 5000, "0.0.0-alpha." + "1" * 5000 + ".1"
    sorted_versions.if_(long, short).then_give([short, long])
    is_equal.if_("0.0.0-" + "1" * 5000, "0.0.0-" + "1" * 5000 + "+other").then_give(True)


def test_prereleases_given_straight_to_the_constructor_compare_by_value():
    compare_prereleases.if_("0001", "1").then_give(0)
    compare_prereleases.if_("000", "0").then_give(0)
    compare_prereleases.if_("02", "10").then_give(-1)
    compare_prereleases.if_("01.2", "1.2").then_give(0)
    compare_prereleases.if_("2a", "10a").then_give(1)
    compare_prereleases.if_("01a", "1a").then_give(-1)
    compare_prereleases.if_("-1", "0").then_give(1)
    compare_prereleases.if_("", None).then_give(0)
    compare_prereleases.if_("١٢", "12").then_give(0)
    compare_prereleases.if_("１２", "13").then_give(-1)
    compare_prereleases.if_("1٢", "12").then_give(0)
    compare_prereleases.if_("٠٠١", "1").then_give(0)


def test_a_superscript_two_is_text_not_a_number():
    # it passes str.isdigit() but int("²") fails, so numbers sort before it
    compare_prereleases.if_("²", "2").then_give(1)
    compare_prereleases.if_("a.²", "b.0").then_give(-1)
    compare_prereleases.if_("a.0", "b.²").then_give(-1)
    expect(
        Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²"), "0.0.0-² < 1.0.0-²"
    ).should.be.true()
    expect(
        Version(1, 2, 3, prerelease="7") < Version(1, 2, 3, prerelease="²"), "1.2.3-7 < 1.2.3-²"
    ).should.be.true()


def test_prereleases_that_were_not_written_in_canonical_form_are_rejected_when_parsing():
    for prerelease in ["01", "01.2", "١٢", "１２"]:
        parse.if_("0.0.0-" + prerelease).then_raise(ValueError)


def test_versions_that_differ_only_in_their_build_are_equal_and_ordered_before_the_release():
    expect(
        Version.parse("0.0.0-" + "1" * 5000) == Version.parse("0.0.0-" + "1" * 5000).replace(build="other"),
        "a long-prerelease version equals itself with another build",
    ).should.be.true()


# ----- comparing a version with things that are not versions ---------------------

equals = spec(lambda text, other: Version.parse(text) == other, says="Version({}) == {}")
differs = spec(lambda text, other: Version.parse(text) != other, says="Version({}) != {}")
older_than = spec(lambda text, other: Version.parse(text) < other, says="Version({}) < {}")
MALFORMED_COLLECTIONS = [
    [],
    (),
    {},
    ["a"],
    (1, "x"),
    (1, 2, 3, 4, 5, 6),
    ["bogus"],
    {"bogus": 1},
    {"major": "a"},
]


def test_a_version_equals_the_same_version_written_as_text_or_a_tuple_but_that_is_deprecated():
    for other in ["1.0.0", (1, 0, 0)]:
        equals.if_("1.0.0", other).then_warn(DeprecationWarning, "Equality comparisons").then_give(True)
        differs.if_("1.0.0", other).then_warn(DeprecationWarning, "Equality comparisons").then_give(False)


def test_a_version_equals_the_same_version_written_as_a_list_or_a_dictionary():
    equals.if_("1.0.0", [1, 0, 0]).then_give(True)
    equals.if_("1.0.0", {"major": 1, "minor": 0, "patch": 0}).then_give(True)


def test_a_version_is_ordered_against_tuples_lists_and_dictionaries():
    older_than.if_("1.0.0", (2, 0, 0)).then_give(True)
    older_than.if_("1.0.0", [2, 0, 0]).then_give(True)
    older_than.if_("1.0.0", {"major": 2, "minor": 0, "patch": 0}).then_give(True)
    older_than.if_("0.4.5-pre.2+build.4", (1, 0, 0)).then_give(True)
    older_than.if_("0.4.5-pre.2+build.4", "1.0.0-pre.2").then_give(True)


def test_a_version_is_never_equal_to_a_malformed_collection():
    for other in MALFORMED_COLLECTIONS:
        warns_for_tuples = isinstance(other, tuple)
        for rule, expected in [(equals, False), (differs, True)]:
            case = rule.if_("1.0.0", other)
            if warns_for_tuples:
                case.then_warn(DeprecationWarning)
            case.then_give(expected)


def test_a_version_cannot_be_ordered_against_a_malformed_collection():
    for other in MALFORMED_COLLECTIONS:
        older_than.if_("1.0.0", other).then_raise(TypeError)


def test_ordering_against_text_that_is_not_a_full_version_is_rejected():
    for other in ["1", "1.0", "1.0.x"]:
        older_than.if_("3.4.5-pre.2+build.4", other).then_raise(ValueError)


def test_a_version_cannot_be_ordered_against_a_number():
    older_than.if_("3.4.5-pre.2+build.4", 1).then_raise(TypeError)
