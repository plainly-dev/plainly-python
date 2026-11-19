"""semver.replace, rewritten with plainly."""

import semver
from semver import Version

from plainly import spec

replace = spec(semver.replace)
replace_in_version = spec(
    lambda text, **parts: str(Version.parse(text).replace(**parts)), name="Version.replace"
)


def test_replace_changes_only_the_parts_you_name():
    replace.if_("3.4.5", major=2).then_give("2.4.5")
    replace.if_("3.4.5", minor=2).then_give("3.2.5")
    replace.if_("3.4.5", major=2, minor=5).then_give("2.5.5")
    replace.if_("3.4.5", major=2, minor=5, patch=10).then_give("2.5.10")


def test_replace_accepts_numbers_as_text():
    replace.if_("3.4.5", major="2").then_give("2.4.5")


def test_replace_can_set_the_prerelease_and_build():
    replace.if_("3.4.5", major=2, minor=5, patch=10, prerelease="rc1").then_give("2.5.10-rc1")
    replace.if_("3.4.5", major=2, minor=5, patch=10, prerelease="rc1", build="b1").then_give("2.5.10-rc1+b1")
    replace.if_("3.4.5-alpha.1.2", build="x1").then_give("3.4.5-alpha.1.2+x1")


def test_replace_keeps_the_prerelease_and_build_it_was_not_told_to_change():
    replace.if_("3.4.5-alpha.1.2", major=2).then_give("2.4.5-alpha.1.2")
    replace.if_("3.4.5+build1", major=2).then_give("2.4.5+build1")


def test_the_version_method_gives_the_same_results():
    replace_in_version.if_("3.4.5", major=2, minor=5).then_give("2.5.5")
    replace_in_version.if_("3.4.5", major=2, minor=5, patch=10).then_give("2.5.10")
    replace_in_version.if_("3.4.5-alpha.1.2", major=2).then_give("2.4.5-alpha.1.2")
    replace_in_version.if_("3.4.5-alpha.1.2", build="x1").then_give("3.4.5-alpha.1.2+x1")
    replace_in_version.if_("3.4.5+build1", major=2).then_give("2.4.5+build1")


def test_replace_rejects_a_part_that_does_not_exist():
    replace.if_("1.2.3", unknown="should_raise").then_raise(TypeError, "unknown")


def test_replace_rejects_numbers_that_are_not_numbers():
    replace_in_version.if_("1.2.3", major="x").then_raise(ValueError)


def test_replace_reports_the_same_error_as_the_constructor_for_a_missing_number():
    for part in ["major", "minor", "patch"]:
        for value in [None, object()]:
            parts = Version.parse("1.2.3").to_dict()
            parts[part] = value
            spec(lambda: Version(**parts), name="Version(...)").if_().then_raise(TypeError)
            replace_in_version.if_("1.2.3", **{part: value}).then_raise(TypeError)
