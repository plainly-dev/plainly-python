TEST = '''
from plainly import spec

def inc(x):
    return x + 1

def test_adds_one_to_a_number():
    spec(inc).if_(1).then_give(2)
    spec(inc).if_(41).then_give(42)
'''


def test_markdown_spec_is_written_and_reads_as_sentences(pytester):
    pytester.makepyfile(test_inc=TEST)
    result = pytester.runpytest("--plainly-md", "SPEC.md")
    result.assert_outcomes(passed=1)
    text = (pytester.path / "SPEC.md").read_text()
    assert "### Adds one to a number" in text
    assert "- inc: if 1, then give 2" in text
    assert "- inc: if 41, then give 42" in text


def test_check_passes_when_the_committed_spec_is_current(pytester):
    pytester.makepyfile(test_inc=TEST)
    pytester.runpytest("--plainly-md", "SPEC.md")
    result = pytester.runpytest("--plainly-check", "SPEC.md")
    assert result.ret == 0


def test_check_fails_when_the_committed_spec_is_stale(pytester):
    pytester.makepyfile(test_inc=TEST)
    pytester.runpytest("--plainly-md", "SPEC.md")
    pytester.makepyfile(test_inc=TEST.replace("(41).then_give(42)", "(41).then_give(42)\n    spec(inc).if_(0).then_give(1)"))
    result = pytester.runpytest("--plainly-check", "SPEC.md")
    assert result.ret == 1
    result.stdout.fnmatch_lines(["*SPEC.md is out of date*"])


PARAMETRISED = '''
import pytest
from plainly import spec

def twice(x):
    return x * 2

@pytest.fixture(params=[1, 2], ids=["one", "two"])
def number(request):
    return request.param

def test_same_story_for_every_value(number):
    spec(twice).if_(0).then_give(0)

def test_a_story_that_differs(number):
    spec(twice).if_(number).then_give(number * 2)
'''


def test_runs_with_the_same_story_are_written_once(pytester):
    pytester.makepyfile(test_twice=PARAMETRISED)
    pytester.runpytest("--plainly-md", "SPEC.md")
    text = (pytester.path / "SPEC.md").read_text()
    assert text.count("### Same story for every value") == 1
    assert "_Runs for each of: one, two._" in text
    assert text.count("- twice: if 0, then give 0") == 1


def test_runs_with_different_stories_are_each_written(pytester):
    pytester.makepyfile(test_twice=PARAMETRISED)
    pytester.runpytest("--plainly-md", "SPEC.md")
    text = (pytester.path / "SPEC.md").read_text()
    assert "### A story that differs [one]" in text
    assert "### A story that differs [two]" in text


HAND_WRITTEN = '''
from plainly import expect, given, spec

def inc(x):
    return x + 1

def test_derived_and_hand_written_wording():
    spec(inc).if_(1).then_give(2)                                   # derived from the call
    spec(inc, says="{} plus one").if_(1).then_give(2)               # written by hand
    spec(lambda x: x + 1).if_(1).then_give(2)                       # an adapter
    expect(inc(1), "one more than one").should.be(2)                # a label
    expect(inc(1)).should.be(2)                                     # label read from the source: derived
'''


def test_hand_written_wording_is_marked_and_counted(pytester):
    pytester.makepyfile(test_hand=HAND_WRITTEN)
    pytester.runpytest("--plainly-md", "SPEC.md")
    text = (pytester.path / "SPEC.md").read_text()
    assert "- inc: if 1, then give 2\n" in text  # no mark: nothing was typed by hand
    assert "- if 1 plus one, then give 2 ✎" in text
    assert "- <lambda>: if 1, then give 2 ✎" in text
    assert "- one more than one should be 2 ✎" in text
    assert "- inc(1) should be 2\n" in text
    assert "covering 3 sentences" in text and "✎ marks wording" in text
    assert '> - says: says "{} plus one" (1 sentence)' in text
    assert "> - label: one more than one (1 sentence)" in text
    assert "> - adapter: lambda at test_hand.py:" in text


def test_a_spec_with_nothing_hand_written_has_no_legend(pytester):
    pytester.makepyfile(test_inc=TEST)
    pytester.runpytest("--plainly-md", "SPEC.md")
    assert "✎" not in (pytester.path / "SPEC.md").read_text()


TOO_LONG = '''
from plainly import spec

def size(x):
    return len(x)

def test_a_huge_input():
    spec(size).if_("9" * 500).then_give(500)
'''


def test_a_sentence_that_was_cut_off_refuses_to_become_a_spec(pytester):
    pytester.makepyfile(test_long=TOO_LONG)
    result = pytester.runpytest("--plainly-md", "SPEC.md")
    assert result.ret == 1
    result.stdout.fnmatch_lines(["*1 sentence(s) were cut off at 100 characters*"])
    assert not (pytester.path / "SPEC.md").exists()


def test_the_width_can_be_raised_when_the_long_value_really_is_the_point(pytester):
    pytester.makepyfile(test_long=TOO_LONG)
    result = pytester.runpytest("--plainly-md", "SPEC.md", "--plainly-width", "600")
    assert result.ret == 0
    assert "9" * 500 in (pytester.path / "SPEC.md").read_text()
