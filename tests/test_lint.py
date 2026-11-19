# Tests of plainly's own internals use plain assert (see AGENTS.md rule 4).
from plainly import lint


def codes(source):
    return [(f.line, f.code) for f in lint.check_source(source, "test_x.py")]


def test_plainly_sentences_pass():
    src = (
        "from plainly import expect, calling\n"
        "def test_a():\n"
        "    expect(1 + 1).should.be(2)\n"
        "    calling(int, 'x').should.raise_(ValueError)\n"
    )
    assert codes(src) == []


def test_bare_assert_is_flagged():
    assert codes("def test_a():\n    assert 1 == 1\n") == [(2, "PL001")]


def test_pytest_raises_is_flagged_in_with_and_call_form():
    src = (
        "import pytest\n"
        "def test_a():\n"
        "    with pytest.raises(ValueError):\n"
        "        int('x')\n"
        "    pytest.raises(ValueError, int, 'x')\n"
    )
    assert codes(src) == [(3, "PL002"), (5, "PL002")]


def test_aliases_and_direct_import_are_flagged():
    src = "import pytest as pt\nfrom pytest import raises as r\npt.raises(E)\nr(E)\n"
    assert codes(src) == [(3, "PL002"), (4, "PL002")]


def test_other_raises_is_not_flagged():
    src = "import other\nother.raises(E)\nraises(E)\n"
    assert codes(src) == []


def test_allow_mark_skips_the_line():
    assert codes("assert x  # plainly: allow\nassert y\n") == [(2, "PL001")]


def test_finding_reads_like_a_compiler_message():
    (f,) = lint.check_source("if 1:\n    assert x\n", "t/test_a.py")
    assert str(f).startswith("t/test_a.py:2:5: PL001 bare assert")


def test_is_test_file():
    assert lint.is_test_file("a/test_cart.py")
    assert lint.is_test_file("cart_test.py")
    assert not lint.is_test_file("cart.py")
    assert not lint.is_test_file("conftest.py")


def test_main_walks_folders_and_sets_exit_code(tmp_path, capsys):
    (tmp_path / "test_bad.py").write_text("assert 1\n")
    (tmp_path / "test_good.py").write_text("from plainly import expect\nexpect(1).should.be(1)\n")
    (tmp_path / "helper.py").write_text("assert 1\n")  # not a test file: skipped
    assert lint.main([str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "test_bad.py:1:1: PL001" in out
    assert "helper.py" not in out
    assert "1 check(s) not written as plainly sentences" in out
    (tmp_path / "test_bad.py").write_text("x = 1\n")
    assert lint.main([str(tmp_path)]) == 0


def test_main_reports_unreadable_files(tmp_path, capsys):
    (tmp_path / "test_broken.py").write_text("def (:\n")
    assert lint.main([str(tmp_path)]) == 2
    assert "cannot check" in capsys.readouterr().err
