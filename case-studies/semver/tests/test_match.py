"""semver.match, rewritten with plainly."""

import semver

from plainly import spec

match = spec(semver.match)


def test_a_version_matches_when_it_satisfies_the_condition():
    match.if_("2.3.7", ">=2.3.6").then_give(True)
    match.if_("2.3.7", "<2.4.0").then_give(True)
    match.if_("2.3.7", ">2.3.5").then_give(True)
    match.if_("2.3.7", "<=2.3.9").then_give(True)
    match.if_("2.3.7", "==2.3.7").then_give(True)


def test_a_version_does_not_match_when_it_fails_the_condition():
    match.if_("2.3.7", ">=2.3.8").then_give(False)
    match.if_("2.3.7", "!=2.3.7").then_give(False)


def test_not_equal():
    match.if_("2.3.7", "!=2.3.8").then_give(True)
    match.if_("2.3.7", "!=2.3.6").then_give(True)
    match.if_("2.3.7", "!=2.3.7").then_give(False)


def test_a_condition_with_no_operator_means_equal():
    match.if_("2.3.7", "2.3.7").then_give(True)
    match.if_("2.3.6", "2.3.6").then_give(True)
    match.if_("2.3.7", "4.3.7").then_give(False)


def test_greater_or_equal_and_less_or_equal_include_the_boundary_itself():
    match.if_("2.3.7", ">=2.3.7").then_give(True)
    match.if_("2.3.7", "<=2.3.7").then_give(True)
    match.if_("2.3.7", ">=2.3.8").then_give(False)
    match.if_("2.3.8", "<=2.3.7").then_give(False)


def test_operators_that_semver_does_not_support_are_rejected():
    match.if_("2.3.7", "=2.3.7").then_raise(ValueError)
    match.if_("2.3.7", "~2.3.7").then_raise(ValueError)
    match.if_("2.3.7", "^2.3.7").then_raise(ValueError)


def test_empty_or_incomplete_conditions_are_rejected():
    match.if_("1.0.0", "").then_raise(ValueError)
    match.if_("1.0.0", "!").then_raise(ValueError)
