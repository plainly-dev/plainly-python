import pytest

from plainly import PlainlyError, given, recorder


class Box(dict):
    """A tiny stateful thing: a dict that holds at most two entries."""

    def __init__(self, size=2):
        super().__init__()
        self.size = size

    def __setitem__(self, key, value):
        if len(self) >= self.size and key not in self:
            del self[next(iter(self))]
        super().__setitem__(key, value)


def sentences():
    return [r.sentence for r in recorder.drain()]


def test_a_story_reads_given_when_and_then():
    recorder.drain()
    box = given(Box, size=2)
    box[1] = "a"
    box[2] = "b"
    box[3] = "c"
    box.then.holds({2: "b", 3: "c"})
    assert sentences() == [
        "given a Box with size=2",
        "when 1 is set to 'a'",
        "and 2 is set to 'b'",
        "and 3 is set to 'c'",
        "then it holds exactly {2: 'b', 3: 'c'}",
    ]


def test_operations_really_happen_and_results_come_back():
    box = given(Box)
    box[1] = "a"
    assert box[1] == "a"
    assert len(box) == 1 and 1 in box
    assert box.pop(1) == "a"
    box.then.holds_nothing()


def test_method_calls_and_their_results_are_written_down():
    recorder.drain()
    box = given(Box)
    box.update({1: "a"})
    box.pop(1)
    box.then.gave("a")
    assert sentences() == [
        "given a Box",
        "when update({1: 'a'}) is called",
        "and pop(1) is called",
        "  giving 'a'",
        "then that gave 'a'",
    ]



class Counter:
    """Its methods return the counter itself, so calls can be chained."""

    def __init__(self):
        self.count = 0

    def add(self, n):
        self.count += n
        return self


def test_a_method_that_returns_its_own_object_lets_a_check_follow_on_the_same_line():
    recorder.drain()
    counter = given(Counter)
    counter.add(2).then.has(count=2)
    counter.add(3).add(1).then.has(count=6)
    assert sentences() == [
        "given a Counter",
        "when add(2) is called",
        "then it has count 2",
        "when add(3) is called",
        "and add(1) is called",
        "then it has count 6",
    ]


def test_a_chained_step_still_fails_loudly():
    counter = given(Counter)
    with pytest.raises(PlainlyError, match="it had {'count': 2}"):
        counter.add(2).then.has(count=3)


def test_expected_errors_are_part_of_the_story():
    recorder.drain()
    box = given(Box)
    with box.raises(KeyError):
        del box[9]
    assert sentences() == ["given a Box", "when 9 is deleted", "then that raises KeyError"]


def test_a_missing_error_fails():
    box = given(Box)
    with pytest.raises(PlainlyError, match="nothing was raised"):
        with box.raises(KeyError):
            box[1] = 1


def test_a_wrong_state_fails_and_says_what_it_was():
    box = given(Box)
    box[1] = "a"
    with pytest.raises(PlainlyError) as info:
        box.then.holds({1: "z"})
    assert "then it holds exactly {1: 'z'}" in str(info.value)
    assert "it held {1: 'a'}" in str(info.value)


def test_other_checks():
    box = given(Box, size=2)
    box[1] = "a"
    box.then.contains(1).lacks(2).has(size=2)
