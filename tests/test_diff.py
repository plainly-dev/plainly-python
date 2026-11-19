from plainly import diff

BASE = """<!-- Generated -->

## tests/test_ordinal.py

### Teens always take th

- ordinal: if '11', then give '11th'
- ordinal: if '12', then give '12th'
- ordinal: if None, then raise TypeError with message containing 'not iterable'

### Non numbers are left alone

- ordinal: if 'x', then give 'x'

### Old story

- ordinal: if 1, then give '1st'
"""


def review(new_text, base=BASE):
    return diff.compare(diff.parse(base), diff.parse(new_text))


def test_nothing_changed():
    report = review(BASE)
    assert not report.weakened
    assert "no change to the spec" in diff.render(report)


def test_a_removed_check_is_flagged_as_weakened():
    report = review(BASE.replace("- ordinal: if '12', then give '12th'\n", ""))
    assert report.weakened
    assert [c.text for c in report.removed_checks] == ["ordinal: if '12', then give '12th'"]
    assert "1 check removed" in diff.render(report)


def test_a_changed_expectation_is_reported_with_before_and_now_but_is_not_weakening():
    report = review(BASE.replace("then give '12th'", "then give '12nd'"))
    assert not report.weakened
    [change] = report.changed
    assert change.old == "ordinal: if '12', then give '12th'" and change.text == "ordinal: if '12', then give '12nd'"
    assert "before:" in diff.render(report)


def test_a_specific_error_widened_to_exception_is_looser():
    report = review(BASE.replace("then raise TypeError with message containing 'not iterable'", "then raise Exception"))
    assert report.weakened
    assert report.looser and "no longer checks the error message" in report.looser[0].why


def test_dropping_only_the_message_check_is_looser():
    report = review(BASE.replace(" with message containing 'not iterable'", ""))
    assert [c.why for c in report.looser] == ["no longer checks the error message"]


def test_a_returned_value_that_became_an_error_is_looser():
    report = review(BASE.replace("if '11', then give '11th'", "if '11', then raise ValueError"))
    assert [c.why for c in report.looser] == ["a returned value became an error"]


def test_a_removed_story_is_weakened_but_a_renamed_one_is_not():
    removed = review(BASE.replace("### Old story\n\n- ordinal: if 1, then give '1st'\n", ""))
    assert removed.weakened and removed.removed_stories[0].story == "Old story"
    renamed = review(BASE.replace("### Old story", "### First, in words"))
    assert not renamed.weakened and not renamed.removed_stories


def test_added_checks_and_stories_are_listed_but_do_not_weaken():
    new = BASE + "\n### Brand new\n\n- ordinal: if 5, then give '5th'\n"
    new = new.replace("- ordinal: if 'x', then give 'x'\n", "- ordinal: if 'x', then give 'x'\n- ordinal: if 'y', then give 'y'\n")
    report = review(new)
    assert not report.weakened
    assert report.added_stories and report.added


def test_new_hand_written_wording_is_called_out():
    new = BASE.replace("- ordinal: if 'x', then give 'x'\n", "- ordinal: if 'x', then give 'x'\n- 'y' stays put ✎\n")
    report = review(new)
    assert [c.text for c in report.new_wordings] == ["'y' stays put"]
    assert "New hand-written wording" in diff.render(report)


def test_the_command_line_fails_only_when_asked_and_only_when_weakened(tmp_path):
    old, new = tmp_path / "old.md", tmp_path / "new.md"
    old.write_text(BASE)
    new.write_text(BASE.replace("- ordinal: if '12', then give '12th'\n", ""))
    assert diff.main([str(old), str(new)]) == 0
    assert diff.main([str(old), str(new), "--fail-on-weakened"]) == 1
    new.write_text(BASE.replace("then give '12th'", "then give '12nd'"))
    assert diff.main([str(old), str(new), "--fail-on-weakened"]) == 0


def test_the_base_can_come_from_git(tmp_path, monkeypatch):
    import subprocess

    monkeypatch.chdir(tmp_path)
    git = lambda *a: subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *a], check=True, capture_output=True)
    git("init", "-q")
    (tmp_path / "SPEC.md").write_text(BASE)
    git("add", "SPEC.md")
    git("commit", "-qm", "base")
    (tmp_path / "SPEC.md").write_text(BASE.replace("- ordinal: if '12', then give '12th'\n", ""))
    assert diff.main(["--base", "HEAD", "SPEC.md", "--fail-on-weakened"]) == 1


def test_the_summary_uses_correct_plurals():
    new = BASE + "\n### One\n\n- a: if 1, then give 1\n\n### Two\n\n- a: if 2, then give 2\n"
    summary = diff.render(review(new)).splitlines()[2]
    assert "2 stories added" in summary
    assert "1 story added" in diff.render(review(BASE + "\n### One\n\n- a: if 1, then give 1\n"))
