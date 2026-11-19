"""humanize.natural_list, rewritten with plainly."""

from humanize import natural_list

from plainly import spec

rule = spec(natural_list)


def test_joins_with_commas_and_a_final_and():
    rule.if_(["1", "2", "3"]).then_give("1, 2 and 3")
    rule.if_(["one", "two", "three"]).then_give("one, two and three")
    rule.if_(["a", "b", "c", "d"]).then_give("a, b, c and d")


def test_two_items_have_no_comma():
    rule.if_(["one", "two"]).then_give("one and two")


def test_one_item_is_returned_as_is():
    rule.if_(["one"]).then_give("one")
    rule.if_(("one",)).then_give("one")


def test_nothing_in_gives_nothing_out():
    rule.if_([]).then_give("")
    rule.if_([""]).then_give("")


def test_items_do_not_have_to_be_strings():
    rule.if_([1, 2, 3]).then_give("1, 2 and 3")
    rule.if_([1, "two"]).then_give("1 and two")
    rule.if_([None, 1.5]).then_give("None and 1.5")


def test_any_iterable_works():
    rule.if_(("one", "two", "three")).then_give("one, two and three")
    rule.if_({"one": 1, "two": 2}.keys()).then_give("one and two")
    rule.if_(x for x in ["one", "two", "three"]).then_give("one, two and three")
    rule.if_(range(1, 4)).then_give("1, 2 and 3")
    rule.if_("abc").then_give("a, b and c")


def test_something_that_is_not_iterable_is_rejected():
    rule.if_(None).then_raise(TypeError)
