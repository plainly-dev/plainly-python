"""semver parsing, rewritten with plainly."""

from semver import Version

from plainly import expect, spec

import semver

from rules import parse, parse_with_optional_minor_and_patch

to_dict = spec(lambda text: Version.parse(text).to_dict(), name="to_dict")


def test_a_full_version_is_split_into_five_parts():
    # (major, minor, patch, prerelease, build)
    parse.if_("1.2.3-alpha.1.2+build.11.e0f985a").then_give((1, 2, 3, "alpha.1.2", "build.11.e0f985a"))
    parse.if_("1.2.3-alpha-1+build.11.e0f985a").then_give((1, 2, 3, "alpha-1", "build.11.e0f985a"))
    parse.if_("1.2.3").then_give((1, 2, 3, None, None))
    parse.if_("1.2.3+build.5").then_give((1, 2, 3, None, "build.5"))


def test_the_parts_are_also_available_as_a_dictionary():
    to_dict.if_("1.2.3-rc.1+build.2").then_give(
        {"major": 1, "minor": 2, "patch": 3, "prerelease": "rc.1", "build": "build.2"}
    )


def test_prereleases_may_start_with_a_zero_when_they_are_not_just_a_number():
    parse.if_("0.1.0-0f").then_give((0, 1, 0, "0f", None))
    parse.if_("0.0.0-0foo.1").then_give((0, 0, 0, "0foo.1", None))
    parse.if_("0.0.0-0foo.1+build.1").then_give((0, 0, 0, "0foo.1", "build.1"))


def test_prereleases_that_are_zero_are_allowed():
    parse.if_("1.2.3-rc.0+build.0").then_give((1, 2, 3, "rc.0", "build.0"))
    parse.if_("1.2.3-rc.0.0+build.0").then_give((1, 2, 3, "rc.0.0", "build.0"))


def test_minor_and_patch_can_be_left_out_when_asked():
    rule = parse_with_optional_minor_and_patch
    rule.if_("1.2-alpha.1.2+build.11.e0f985a").then_give((1, 2, 0, "alpha.1.2", "build.11.e0f985a"))
    rule.if_("1-alpha-1+build.11.e0f985a").then_give((1, 0, 0, "alpha-1", "build.11.e0f985a"))
    rule.if_("0.1-0f").then_give((0, 1, 0, "0f", None))
    rule.if_("0-0foo.1").then_give((0, 0, 0, "0foo.1", None))
    rule.if_("0-0foo.1+build.1").then_give((0, 0, 0, "0foo.1", "build.1"))


def test_numbers_may_not_have_leading_zeros():
    for text in ["01.2.3", "1.02.3", "1.2.03"]:
        parse.if_(text).then_raise(ValueError)


def test_text_that_is_not_a_version_is_rejected():
    for text in ["foo", "1.0", "1.x", "", "1.2.3.4"]:
        parse.if_(text).then_raise(ValueError)


def test_equal_versions_have_equal_hashes():
    first = Version.parse("1.2.3-alpha.1.2+build.11.e0f985a")
    second = Version.parse("1.2.3-alpha.1.2+build.22.a589f0e")  # only the build differs
    expect(first == second, "1.2.3-alpha.1.2+build.11 == 1.2.3-alpha.1.2+build.22").should.be.true()
    expect(hash(first) == hash(second), "their hashes are equal").should.be.true()
    expect(len({first, second}), "number of distinct versions in a set").should.be(1)


def test_prereleases_that_compare_equal_have_equal_hashes():
    for a, b in [("007", "7"), ("alpha.007.beta", "alpha.7.beta"), ("٧", "7"), ("", None)]:
        v1, v2 = Version(1, 2, 3, prerelease=a), Version(1, 2, 3, prerelease=b)
        expect(v1 == v2, f"prerelease {a!r} == prerelease {b!r}").should.be.true()
        expect(hash(v1) == hash(v2), f"hash of prerelease {a!r} == hash of prerelease {b!r}").should.be.true()


def test_a_version_prints_as_the_text_it_was_parsed_from():
    text = "1.2.3-alpha.1.2+build.11.e0f985a"
    expect(str(Version.parse(text)), f"str(Version.parse({text!r}))").should.be(text)


legacy_parse = spec(semver.parse, name="semver.parse (deprecated)")
legacy_parse_version_info = spec(
    lambda text: str(semver.parse_version_info(text)), name="semver.parse_version_info (deprecated)"
)


def test_the_old_function_parse_gives_a_dictionary_and_warns():
    legacy_parse.if_("1.2.3-rc.1+build.2").then_warn(DeprecationWarning, "semver.parse").then_give(
        {"major": 1, "minor": 2, "patch": 3, "prerelease": "rc.1", "build": "build.2"}
    )


def test_the_old_function_parse_version_info_gives_a_version_and_warns():
    legacy_parse_version_info.if_("1.2.3-rc.1+build.2").then_warn(DeprecationWarning).then_give(
        "1.2.3-rc.1+build.2"
    )


def test_only_text_or_bytes_can_be_parsed():
    parse.if_(123).then_raise(TypeError, "not expecting type")
    parse.if_(None).then_raise(TypeError, "not expecting type")
