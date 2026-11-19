"""semver.Version as an object, rewritten with plainly: building, indexing, immutability, strict parsing, compatibility."""

from semver import Version

from plainly import expect, spec

from rules import parse, parse_with_optional_minor_and_patch

VERSION = "1.2.3-alpha.1.2+build.11.e0f985a"

is_valid = spec(Version.is_valid)
is_compatible = spec(
    lambda old, new: Version.parse(old).is_compatible(Version.parse(new)), says="{} can be replaced by {}"
)
part_at = spec(lambda text, index: Version.parse(text)[index], says="{0}[{1}]")
increment = spec(Version._increment_string, name="increment the number at the end")


def test_incrementing_the_number_at_the_end_of_text():
    increment.if_("rc").then_give("rc")
    increment.if_("rc.1").then_give("rc.2")
    increment.if_("2x").then_give("3x")


def test_numbers_may_not_be_negative():
    for kwargs in [
        {"major": -1},
        {"major": 1, "minor": -2},
        {"major": 1, "minor": 2, "patch": -3},
        {"major": 1, "minor": -2, "patch": 3},
    ]:
        spec(Version, name="Version").if_(**kwargs).then_raise(ValueError, "is negative")


def test_major_minor_and_patch_may_be_given_as_text_numbers():
    version = Version("1", "2", "3")
    expect((version.major, version.minor, version.patch), "Version('1', '2', '3') as numbers").should.be(
        (1, 2, 3)
    )
    expect(version.prerelease, "Version('1', '2', '3').prerelease").should.be.none()
    expect(version.build, "Version('1', '2', '3').build").should.be.none()


def test_text_that_is_not_a_number_is_rejected_for_major_minor_and_patch():
    spec(Version, name="Version").if_("a").then_raise(ValueError)
    spec(Version, name="Version").if_(1, "a").then_raise(ValueError)
    spec(Version, name="Version").if_(1, 2, "a").then_raise(ValueError)


def test_prerelease_and_build_may_be_given_as_numbers_and_become_text():
    version = Version(1, 2, 3, 4, 5)
    expect((version.prerelease, version.build), "Version(1, 2, 3, 4, 5) prerelease and build").should.be(
        ("4", "5")
    )


def test_is_valid_says_whether_text_is_a_version():
    is_valid.if_("1.0.0").then_give(True)
    is_valid.if_("foo").then_give(False)


def test_is_valid_also_reads_bytes():
    is_valid.if_(b"1.0.0").then_give(True)
    is_valid.if_(b"foo").then_give(False)
    is_valid.if_("1.0.0".encode("UTF-8")).then_give(True)
    is_valid.if_(b"\xff").then_give(False)


def test_a_version_converts_to_a_dictionary_and_a_tuple_and_can_be_iterated():
    version = Version.parse(VERSION)
    expect(list(version.to_dict()), f"the keys of Version.parse({VERSION!r}).to_dict()").should.be(
        ["major", "minor", "patch", "prerelease", "build"]
    )
    expect(version.to_tuple(), f"Version.parse({VERSION!r}).to_tuple()").should.be(
        (1, 2, 3, "alpha.1.2", "build.11.e0f985a")
    )
    expect(tuple(version), f"tuple(Version.parse({VERSION!r}))").should.be(
        (1, 2, 3, "alpha.1.2", "build.11.e0f985a")
    )


def test_a_version_is_read_only():
    for attribute, value in [
        ("major", 9),
        ("minor", 9),
        ("patch", 9),
        ("prerelease", "alpha.9.9"),
        ("build", "build.99.e0f985a"),
    ]:
        spec(
            lambda text, new, attribute=attribute: setattr(Version.parse(text), attribute, new),
            says="{0}." + attribute + " = {1}",
        ).if_(VERSION, value).then_raise(AttributeError, f"attribute '{attribute}' is readonly")
    spec(
        lambda text: setattr(Version.parse(text), "new_attribute", "forbidden"),
        says="{}.new_attribute = 'forbidden'",
    ).if_(VERSION).then_raise(AttributeError, "has no attribute 'new_attribute'")


def test_parts_are_read_by_position():
    part_at.if_("1.2.3-rc.0+build.0", 0).then_give(1)
    part_at.if_("1.2.3-rc.0+build.0", 1).then_give(2)
    part_at.if_("1.2.3-rc.0+build.0", 2).then_give(3)
    part_at.if_("1.2.3-rc.0+build.0", 3).then_give("rc.0")
    part_at.if_("1.2.3-rc.0+build.0", 4).then_give("build.0")
    part_at.if_("1.2.3-rc.0", 3).then_give("rc.0")
    part_at.if_("1.0.2", 1).then_give(0)


def test_parts_are_read_by_slice():
    part_at.if_("1.2.3-rc.0+build.0", slice(0, 5)).then_give((1, 2, 3, "rc.0", "build.0"))
    part_at.if_("1.2.3-rc.0+build.0", slice(0, 4)).then_give((1, 2, 3, "rc.0"))
    part_at.if_("1.2.3-rc.0+build.0", slice(0, 3)).then_give((1, 2, 3))
    part_at.if_("1.2.3-rc.0+build.0", slice(0, 2)).then_give((1, 2))
    part_at.if_("1.2.3-rc.0+build.0", slice(3, 5)).then_give(("rc.0", "build.0"))
    part_at.if_("1.2.3-rc.0", slice(0, 4)).then_give((1, 2, 3, "rc.0"))
    part_at.if_("1.2.3", slice(0, 10)).then_give((1, 2, 3))
    part_at.if_("1.2.3-rc.0+build.0", slice(3)).then_give((1, 2, 3))
    part_at.if_("1.2.3-rc.0+build.0", slice(0, 5, 2)).then_give((1, 3, "build.0"))
    part_at.if_("1.2.3-rc.0+build.0", slice(None, 5, 2)).then_give((1, 3, "build.0"))
    part_at.if_("1.2.3-rc.0+build.0", slice(5, 0, -2)).then_give(("build.0", 3))
    part_at.if_("1.2.0-rc.0+build.0", slice(3)).then_give((1, 2, 0))


def test_a_part_that_does_not_exist_is_an_index_error():
    for text, index in [
        ("1.2.3", 3),
        ("1.2.3", 4),
        ("1.2.3", 5),
        ("1.2.3-rc.0", 5),
        ("1.2.3-rc.0", 6),
        ("1.2.3", slice(3, 4)),
        ("1.2.3", slice(4, 5)),
        ("1.2.3-rc.0", slice(5, 6)),
    ]:
        part_at.if_(text, index).then_raise(IndexError, "Version part undefined")


def test_negative_positions_are_not_allowed():
    for index in [-1, -2, slice(-2, 2), slice(2, -2), slice(-2, -2)]:
        part_at.if_("1.2.3", index).then_raise(IndexError, "Version index cannot be negative")


def test_positions_must_be_numbers():
    for key in [None, "1", 1.0]:
        part_at.if_("1.2.3", key).then_raise(TypeError)


class Position:
    def __init__(self, value):
        self.value = value

    def __index__(self):
        return self.value

    def __repr__(self):
        return f"Position({self.value})"


def test_anything_that_works_as_an_index_can_be_used_as_a_position():
    part_at.if_("1.2.3", Position(1)).then_give(2)
    part_at.if_("1.2.3", slice(Position(0), Position(2))).then_give((1, 2))
    part_at.if_("1.2.3", Position(-1)).then_raise(IndexError)


def test_compatible_versions_can_replace_each_other():
    is_compatible.if_("1.2.3", "1.2.3").then_give(True)
    is_compatible.if_("1.2.3", "1.2.4").then_give(True)
    is_compatible.if_("1.2.4", "1.2.3").then_give(True)
    is_compatible.if_("1.2.3-rc.0", "1.2.4-rc.0").then_give(True)
    is_compatible.if_("0.1.0", "0.1.0").then_give(True)


def test_incompatible_versions_cannot_replace_each_other():
    is_compatible.if_("1.1.0", "1.0.0").then_give(False)
    is_compatible.if_("2.0.0", "1.5.0").then_give(False)
    is_compatible.if_("1.2.3-rc.1", "1.2.3-rc.0").then_give(False)
    is_compatible.if_("1.2.3-rc.1", "1.2.4-rc.0").then_give(False)
    is_compatible.if_("0.1.0", "0.1.1").then_give(False)
    is_compatible.if_("1.0.0", "1.0.0-rc1").then_give(False)
    is_compatible.if_("1.0.0-rc1", "1.0.0").then_give(False)


def test_the_build_is_ignored_when_checking_compatibility():
    is_compatible.if_("0.1.2+build.1", "0.1.2+build.2").then_give(True)
    is_compatible.if_("1.2.3+build.1", "1.2.3+build.2").then_give(True)


def test_only_a_version_can_be_checked_for_compatibility():
    for wrong in ["wrongtype", {"a": 2}, []]:
        spec(lambda other: Version(1, 2, 3).is_compatible(other), says="1.2.3 can be replaced by {}").if_(
            wrong
        ).then_raise(TypeError, "Expected a Version type")


def test_a_subclass_of_version_is_accepted():
    class CustomVersion(Version): ...

    expect(
        CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)),
        "a CustomVersion(1, 0, 0) is compatible with Version(1, 0, 0)",
    ).should.be.true()


# ----- strict parsing --------------------------------------------------------


def test_text_with_characters_outside_the_semver_alphabet_is_rejected():
    for text in [
        "1.2.3\n",
        "1.2.3-rc.1\n",
        "1.2.3+build.1\n",
        "1٢.2.3",
        "1.2٣.3",
        "1.2.3٤",
        "1.2.3-1٢",
        "1.2.3-١alpha",
    ]:
        parse.if_(text).then_raise(ValueError)


def test_the_same_applies_when_minor_and_patch_are_optional():
    for text in ["1.2.3\n", "1\n", "1.2\n", "1٢", "1.2٣"]:
        parse_with_optional_minor_and_patch.if_(text).then_raise(ValueError)


def test_is_valid_rejects_characters_outside_the_semver_alphabet():
    for text in ["1.2.3\n", "1٢.2.3", "1.2.3-١alpha"]:
        is_valid.if_(text).then_give(False)
