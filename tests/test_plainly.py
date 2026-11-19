import pytest

from plainly import PlainlyError, calling, expect, recorder


def boom(x):
    raise KeyError("missing " + str(x))


def test_be_passes_and_fails():
    expect(8).should.be(8)
    with pytest.raises(PlainlyError) as info:
        expect(7).should.be(8)
    assert "should be 8" in str(info.value)
    assert "it was 7" in str(info.value)


def test_must_and_negation_wording():
    recorder.drain()
    expect(3).must.not_.be(4)
    assert recorder.drain()[0].sentence == "3 must not be 4"


def test_label_comes_from_source():
    recorder.drain()
    expect(sum([3, 5])).should.be(8)
    assert recorder.drain()[0].sentence == "sum([3, 5]) should be 8"


def test_raise_by_class_and_by_name():
    calling(boom, 1).should.raise_(KeyError)
    calling(boom, 1).should.raise_("KeyError")
    calling(boom, 1).should.raise_(LookupError)  # subclasses count
    calling(boom, 1).should.raise_(KeyError, message="missing 1")


def test_raise_fails_when_nothing_raised():
    with pytest.raises(PlainlyError) as info:
        calling(len, "abc").should.raise_(ValueError)
    assert "without raising" in str(info.value)


def test_raise_wrong_type_fails():
    with pytest.raises(PlainlyError):
        calling(boom, 1).should.raise_(ValueError)


def test_negated_raise():
    calling(len, "abc").should.not_.raise_(ValueError)


def test_unexpected_exception_is_reported_readably():
    with pytest.raises(PlainlyError) as info:
        calling(boom, 2).should.be(1)
    assert "it raised KeyError" in str(info.value)


def test_calling_label_includes_args():
    recorder.drain()
    calling(pow, 2, 3).should.return_(8)
    assert recorder.drain()[0].sentence == "pow(2, 3) should return 8"


def test_comparison_matchers():
    expect(5).should.be.greater_than(3)
    expect(5).should.be.at_least(5)
    expect(5).should.be.between(1, 10)
    expect(0.1 + 0.2).should.be.close_to(0.3, 1e-9)
    expect(None).should.be.none()
    expect("x").should.be.instance_of(str)
    expect(2).should.be.one_of(1, 2, 3)
    expect([]).should.be.empty()


def test_collection_and_text_matchers():
    expect([1, 2, 3]).should.contain(2)
    expect([1, 2, 3]).should.have_length(3)
    expect("hello").should.start_with("he")
    expect("hello").should.end_with("lo")
    expect("order-42").should.match(r"\d+")
    expect(10).should.satisfy(lambda v: v % 2 == 0, "is even")


def test_raise_on_plain_value_is_a_clear_usage_error():
    with pytest.raises(TypeError):
        expect(1).should.raise_(ValueError)
