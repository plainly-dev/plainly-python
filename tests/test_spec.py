import pytest

from plainly import PlainlyError, method, recorder, spec


def double(x, times=2):
    if x < 0:
        raise ValueError("negative")
    return x * times


def sentences():
    return [r.sentence for r in recorder.drain()]


def test_examples_read_as_if_then_sentences():
    recorder.drain()
    rule = spec(double)
    rule.if_(2).then_give(4)
    rule.if_(2, times=5).then_give(10)
    rule.if_(-1).then_raise(ValueError, "negative")
    rule.if_(3).then_not_raise()
    assert sentences() == [
        "double: if 2, then give 4",
        "double: if 2, times=5, then give 10",
        "double: if -1, then raise ValueError with message containing 'negative'",
        "double: if 3, then not raise Exception",
    ]


def test_strings_keep_their_quotes_so_text_and_numbers_differ():
    recorder.drain()
    spec(str).if_(11).then_give("11")
    assert sentences() == ["str: if 11, then give '11'"]


def test_failure_names_the_example():
    with pytest.raises(PlainlyError) as info:
        spec(double).if_(3).then_give(7)
    assert "double: if 3, then give 7" in str(info.value)
    assert "it was 6" in str(info.value)


def test_must_wording_is_kept():
    recorder.drain()
    spec(double).must.if_(2).then_give(4)
    spec(double).must.if_(3).then_not_raise()
    assert sentences() == ["double: if 2, then must give 4", "double: if 3, then must not raise Exception"]


def test_no_arguments_reads_naturally():
    recorder.drain()
    spec(list).if_().then_give([])
    assert sentences() == ["list: if called with nothing, then give []"]


def test_a_single_tuple_is_one_argument():
    spec(len).if_((1, 2, 3)).then_give(3)


def test_says_writes_the_condition_yourself():
    recorder.drain()
    lower = spec(lambda a, b: a < b, says="{} < {}")
    lower.if_(1, 2).then_give(True)
    lower.if_("b", "a").then_give(False)
    assert sentences() == ["if 1 < 2, then give True", "if 'b' < 'a', then give False"]


def test_name_and_show_change_the_wording():
    recorder.drain()
    spec(lambda x: x * 2, name="twice", show=str).if_(3).then_give(6)
    assert sentences() == ["twice: if 3, then give 6"]


def test_method_adapter_calls_a_method_on_the_object_built_from_the_first_input():
    recorder.drain()
    shout = spec(method(str.strip, "upper"))  # strip first, then .upper()
    shout.if_("  hi ").then_give("HI")
    ends = spec(method(str, "endswith"))
    ends.if_("hello", "lo").then_give(True)
    assert sentences() == ["upper: if '  hi ', then give 'HI'", "endswith: if 'hello', 'lo', then give True"]


def noisy(x):
    import warnings

    warnings.warn("old way, use new_way", DeprecationWarning)
    return x


def test_then_warn_checks_for_a_warning_and_the_result_after_it():
    recorder.drain()
    rule = spec(noisy)
    rule.if_(5).then_warn(DeprecationWarning, "new_way").then_give(5)
    assert sentences() == [
        "noisy: if 5, then warn DeprecationWarning with message containing 'new_way'",
        "noisy: if 5, then give 5",
    ]


def test_then_warn_fails_when_nothing_is_warned():
    with pytest.raises(PlainlyError) as info:
        spec(len).if_("abc").then_warn(DeprecationWarning)
    assert "it issued no warning" in str(info.value)


def test_a_long_value_is_cut_with_a_mark_that_cannot_be_missed():
    from plainly import subjects

    shown = subjects._short("x" * 300)
    assert len(shown) == subjects.WIDTH and shown.endswith(subjects.CUT)


def test_records_say_why_their_wording_is_hand_written():
    recorder.drain()
    spec(lambda x: x, says="{} itself").if_(1).then_give(1)
    spec(double).if_(2).then_give(4)
    assert [r.prose for r in recorder.drain()] == ["says, adapter", ""]
