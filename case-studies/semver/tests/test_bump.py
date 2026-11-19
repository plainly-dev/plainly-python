"""semver bumping, rewritten with plainly."""

import semver
from semver import Version

from plainly import spec

from rules import on_version

bump_major = spec(semver.bump_major)
bump_minor = spec(semver.bump_minor)
bump_patch = spec(semver.bump_patch)
bump_prerelease = spec(semver.bump_prerelease)
bump_build = spec(semver.bump_build)

next_version = on_version("next_version")
version_bump_prerelease = on_version("bump_prerelease")
version_bump_build = on_version("bump_build")


def test_each_part_can_be_bumped_and_the_lower_parts_reset():
    bump_major.if_("3.4.5").then_give("4.0.0")
    bump_minor.if_("3.4.5").then_give("3.5.0")
    bump_patch.if_("3.4.5").then_give("3.4.6")


def test_bumping_drops_the_prerelease_and_build():
    bump_patch.if_("3.4.5-rc1+build4").then_give("3.4.6")
    bump_prerelease.if_("3.4.5-rc.1+build.4").then_give("3.4.5-rc.2")


def bumped(text, steps):
    """Apply the bumps in order: "major then minor" calls bump_major() then bump_minor()."""
    version = Version.parse(text)
    for step in steps.split(" then "):
        version = getattr(version, f"bump_{step}")()
    return str(version)


def test_bumps_can_be_chained():
    chain = spec(bumped, says="{0} bumped by {1}")
    chain.if_("3.4.5", "major then minor").then_give("4.1.0")
    chain.if_("3.4.5", "minor then patch").then_give("3.5.1")
    chain.if_("3.4.5-rc.1", "patch then prerelease").then_give("3.4.6-rc.1")
    # bumping the prerelease drops the old build, so the build starts again at 1.
    # (upstream expected "+build.2" here, but compared with ==, which ignores build metadata)
    chain.if_("3.4.5-rc.1+build.1", "prerelease then build").then_give("3.4.5-rc.2+build.1")
    chain.if_("3.4.5-rc.1+build.1", "prerelease then build then build").then_give("3.4.5-rc.2+build.2")


def test_bumping_the_prerelease_counts_up():
    bump_prerelease.if_("3.4.5-rc.9").then_give("3.4.5-rc.10")
    bump_prerelease.if_("3.4.5").then_give("3.4.5-rc.1")
    bump_prerelease.if_("3.4.5", "dev").then_give("3.4.5-dev.1")


def test_bumping_the_prerelease_of_a_final_version_can_use_an_empty_or_missing_token():
    version_bump_prerelease.if_("3.4.5", "").then_give("3.4.5-1")
    version_bump_prerelease.if_("3.4.5", None).then_give("3.4.5-rc.1")
    version_bump_prerelease.if_("3.4.5", bump_when_empty=True).then_give("3.4.6-rc.1")


def test_a_prerelease_that_does_not_end_in_a_number_gets_a_zero_added():
    version_bump_prerelease.if_("3.4.5-rc1", None).then_give("3.4.5-rc1.0")
    version_bump_prerelease.if_("3.4.5-rc9", None).then_give("3.4.5-rc9.0")


def test_a_prerelease_that_is_only_a_number_just_counts_up():
    version_bump_prerelease.if_("1.2.3-3").then_give("1.2.3-4")
    version_bump_prerelease.if_("1.2.3-9").then_give("1.2.3-10")


def test_bumping_the_build_counts_up_and_does_not_change_precedence():
    bump_build.if_("3.4.5-rc.1+build.9").then_give("3.4.5-rc.1+build.10")
    bump_build.if_("3.4.5-rc.1+0009.dev").then_give("3.4.5-rc.1+0010.dev")
    bump_build.if_("3.4.5-rc.1").then_give("3.4.5-rc.1+build.1")
    bump_build.if_("3.4.5").then_give("3.4.5+build.1")


def test_bumping_the_build_without_a_build_uses_the_token():
    version_bump_build.if_("3.4.5", "").then_give("3.4.5+1")
    version_bump_build.if_("3.4.5", None).then_give("3.4.5+build.1")
    version_bump_build.if_("1.2.3", "b").then_give("1.2.3+b.1")


def test_a_build_without_digits_gets_a_zero_added():
    version_bump_build.if_("1.2.3+alpha").then_give("1.2.3+alpha.0")
    version_bump_build.if_("1.2.3+exp.sha").then_give("1.2.3+exp.sha.0")
    version_bump_build.if_("1.2.3+alpha", "b").then_give(
        "1.2.3+alpha.0"
    )  # the token is only used when there is no build
    version_bump_build.if_("1.2.3+build.9").then_give("1.2.3+build.10")
    version_bump_build.if_("1.2.3+alpha.1").then_give("1.2.3+alpha.2")


def test_a_digitless_build_keeps_counting_when_bumped_again():
    spec(bumped, says="{0} bumped by {1}").if_("1.2.3+alpha", "build then build").then_give("1.2.3+alpha.1")


def test_next_version_picks_the_smallest_version_that_is_newer():
    next_version.if_("1.0.4-rc.1", "major").then_give("2.0.0")
    next_version.if_("1.1.0-rc.1", "major").then_give("2.0.0")
    next_version.if_("1.1.4-rc.1", "major").then_give("2.0.0")
    next_version.if_("1.2.3", "major").then_give("2.0.0")
    next_version.if_("1.0.0-rc.1", "major").then_give("1.0.0")
    next_version.if_("0.2.0-rc.1", "minor").then_give("0.2.0")
    next_version.if_("0.2.5-rc.1", "minor").then_give("0.3.0")
    next_version.if_("1.3.1", "minor").then_give("1.4.0")
    next_version.if_("1.3.2", "patch").then_give("1.3.3")
    next_version.if_("0.1.5-rc.2", "patch").then_give("0.1.5")
    next_version.if_("0.1.4", "prerelease").then_give("0.1.5-rc.1")
    next_version.if_("0.1.5-rc.1", "prerelease").then_give("0.1.5-rc.2")


def test_next_version_finishes_a_prerelease_instead_of_skipping_past_it():
    next_version.if_("0.2.0-rc.1", "patch").then_give("0.2.0")
    next_version.if_("1.0.0-rc.1", "patch").then_give("1.0.0")
    next_version.if_("1.0.0-rc.1", "minor").then_give("1.0.0")


def test_next_version_on_a_version_that_only_has_build_metadata_really_bumps():
    # build metadata does not affect precedence, so stripping it would not be a new version
    next_version.if_("1.2.3+build.5", "patch").then_give("1.2.4")
    next_version.if_("1.0.0+build.5", "patch").then_give("1.0.1")
    next_version.if_("0.1.4+build.5", "patch").then_give("0.1.5")
    next_version.if_("1.2.0+build.5", "minor").then_give("1.3.0")
    next_version.if_("1.0.0+build.5", "major").then_give("2.0.0")


def test_next_version_drops_the_build_when_finishing_a_prerelease():
    next_version.if_("1.2.3-rc.1+build.5", "patch").then_give("1.2.3")
    next_version.if_("1.2.3-rc.1+build.5", "prerelease").then_give("1.2.3-rc.2")
    next_version.if_("1.2.3-rc1+build.5", "prerelease").then_give("1.2.3-rc2")


def test_next_version_follows_the_whole_token_family():
    next_version.if_("1.2.3-alpha.beta.1+build.7", "prerelease", "alpha.beta").then_give("1.2.3-alpha.beta.2")
    next_version.if_("1.2.3-alpha.beta.gamma.1", "prerelease", "alpha").then_give("1.2.3-alpha.beta.gamma.2")
    next_version.if_("1.2.3-rc3", "prerelease", "rc").then_give("1.2.3-rc4")
    next_version.if_("1.2.3-rc.3", "prerelease", "rc").then_give("1.2.3-rc.4")
    next_version.if_("1.2.3-alphaXbeta9", "prerelease", "alpha.beta").then_give("1.2.4-alpha.beta.1")


def test_next_version_with_an_empty_or_missing_token_keeps_the_existing_family():
    next_version.if_("1.2.3-alpha.beta.1", "prerelease", None).then_give("1.2.3-alpha.beta.2")
    next_version.if_("1.2.3-alpha.beta.1", "prerelease", "").then_give("1.2.3-alpha.beta.2")


def test_next_version_ignores_the_token_for_major_minor_and_patch():
    next_version.if_("1.2.3", "major", "rc.").then_give("2.0.0")
    next_version.if_("1.2.3", "minor", "rc+build").then_give("1.3.0")
    next_version.if_("1.2.3", "patch", "rc..next").then_give("1.2.4")


def test_next_version_never_goes_backwards_for_legacy_counters_like_rc9():
    next_version.if_("1.2.3-rc9", "prerelease", "rc").then_give("1.2.4-rc10")
    next_version.if_("1.2.3-rc99", "prerelease", "rc").then_give("1.2.4-rc100")
    next_version.if_("1.2.3-rc999+build.7", "prerelease", "rc").then_give("1.2.4-rc1000")
    next_version.if_("1.2.3-beta9", "prerelease", "beta").then_give("1.2.4-beta10")
    next_version.if_("1.2.3-alpha.beta9", "prerelease", "alpha.beta").then_give("1.2.4-alpha.beta10")
    next_version.if_("1.2.3-0rc9", "prerelease", "0rc").then_give("1.2.4-0rc10")
    next_version.if_("0.0.0-rc9", "prerelease", "rc").then_give("0.0.1-rc10")
    next_version.if_("1.2.3-rc8", "prerelease", "rc").then_give("1.2.3-rc9")
    next_version.if_("1.2.3-rc98", "prerelease", "rc").then_give("1.2.3-rc99")
    next_version.if_("1.2.3-rc099", "prerelease", "rc").then_give("1.2.3-rc100")
    next_version.if_("1.2.3-rc09", "prerelease", "rc").then_give("1.2.3-rc10")
    next_version.if_("1.2.3-rc.9", "prerelease", "rc").then_give("1.2.3-rc.10")


def test_next_version_rejects_a_part_that_does_not_exist():
    next_version.if_("1.0.1", "invalid").then_raise(ValueError)


def test_tokens_that_would_make_an_invalid_version_are_rejected():
    for token in ["[", "rc.", "rc+build", "rc..next", "rc.01", "01", "ré"]:
        next_version.if_("1.2.3-rc.1", "prerelease", token).then_raise(ValueError)
    for token in ["rc+build", "rc/", "rc.", ".rc", "rc..2", "rc.05"]:
        version_bump_prerelease.if_("1.0.0", token).then_raise(ValueError)
    for token in ["bu/ild", "build+meta", "bu ild", "build.", ".build", "build..2"]:
        version_bump_build.if_("1.0.0", token).then_raise(ValueError)


def test_valid_tokens_are_used_as_they_are():
    version_bump_build.if_("1.0.0", "build").then_give("1.0.0+build.1")
    version_bump_build.if_("1.0.0", "b").then_give("1.0.0+b.1")
    version_bump_build.if_("1.0.0", "build.2").then_give("1.0.0+build.2.1")
    version_bump_build.if_("1.0.0", "dev-1").then_give("1.0.0+dev-1.1")
    version_bump_prerelease.if_("1.0.0", "rc").then_give("1.0.0-rc.1")
    version_bump_prerelease.if_("1.0.0", "rc.1").then_give("1.0.0-rc.1.1")
    version_bump_prerelease.if_("1.0.0", "dev-1").then_give("1.0.0-dev-1.1")
    version_bump_prerelease.if_("1.0.0", "alpha.0").then_give("1.0.0-alpha.0.1")


def test_switching_to_a_different_token_starts_a_new_family_and_stays_newer():
    next_version.if_("1.2.3-rc.1", "prerelease", "alpha").then_give("1.2.4-alpha.1")
    next_version.if_("1.2.3-beta.3", "prerelease", "alpha").then_give("1.2.4-alpha.1")
    next_version.if_("1.2.3-rc.1+build.7", "prerelease", "dev").then_give("1.2.4-dev.1")
    next_version.if_("1.2.3-rc3", "prerelease", "alpha").then_give("1.2.4-alpha.1")
    next_version.if_("1.2.3-rc.1", "prerelease", "2").then_give("1.2.4-2.1")
    next_version.if_("1.2.3-alpha.4", "prerelease", "rc").then_give("1.2.3-rc.1")


def test_old_style_prereleases_without_a_dot_keep_counting():
    next_version.if_("0.1.2-rc3", "prerelease").then_give("0.1.2-rc4")
    next_version.if_("1.2.3-rc9", "prerelease").then_give("1.2.4-rc10")
    next_version.if_("0.1.2-rc.3", "prerelease").then_give("0.1.2-rc.4")
    next_version.if_("1.2.3-alpha1", "prerelease").then_give("1.2.3-rc.1")
    next_version.if_("1.2.3-beta2", "prerelease", "beta").then_give("1.2.3-beta3")
    next_version.if_("1.2.3-rc3+build.5", "prerelease").then_give("1.2.3-rc4")
