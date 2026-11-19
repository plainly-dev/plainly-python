"""semver.max_ver and min_ver, rewritten with plainly."""

from semver import max_ver, min_ver

from plainly import spec

newest = spec(max_ver)
oldest = spec(min_ver)


def test_newest_of_two_versions():
    newest.if_("3.4.5", "4.0.2").then_give("4.0.2")
    newest.if_("4.0.2", "3.4.5").then_give("4.0.2")


def test_oldest_of_two_versions():
    oldest.if_("3.4.5", "4.0.2").then_give("3.4.5")
    oldest.if_("4.0.2", "3.4.5").then_give("3.4.5")


def test_two_equal_versions_give_that_version():
    newest.if_("3.4.5", "3.4.5").then_give("3.4.5")
    oldest.if_("3.4.5", "3.4.5").then_give("3.4.5")


def test_prereleases_are_ordered_by_the_semver_rules():
    # numbers are compared as numbers, so rc.2 is older than rc.10
    oldest.if_("1.2.3-rc.2", "1.2.3-rc.10").then_give("1.2.3-rc.2")
    # without a dot rc2 and rc10 are text, compared character by character: "rc10" sorts before "rc2"
    oldest.if_("1.2.3-rc2", "1.2.3-rc10").then_give("1.2.3-rc10")
    # text is compared in ASCII order: uppercase comes before lowercase
    oldest.if_("1.2.3-Rc10", "1.2.3-rc10").then_give("1.2.3-Rc10")
    # a number is always older than text
    oldest.if_("1.2.3-2", "1.2.3-rc").then_give("1.2.3-2")
    # with equal beginnings, the shorter list is older
    oldest.if_("1.2.3-rc.2.1", "1.2.3-rc.2").then_give("1.2.3-rc.2")
    oldest.if_("1.0.0-alpha", "1.0.0-alpha.1").then_give("1.0.0-alpha")
    # a prerelease is older than the release itself
    oldest.if_("1.2.3", "1.2.3-1").then_give("1.2.3-1")
