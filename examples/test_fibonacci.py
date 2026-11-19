"""What a reviewer should see when an AI writes tests: one line, one rule."""
from plainly import calling, expect

from fibonacci import fib


def test_rejects_invalid_input():
    calling(fib, -1).should.raise_(ValueError)
    calling(fib, 2.5).should.raise_(ValueError)
    calling(fib, "7").should.raise_(ValueError, message="integer")


def test_base_cases():
    expect(fib(0)).should.be(0)
    expect(fib(1)).should.be(1)


def test_known_values():
    expect(fib(2)).must.be(1)
    expect(fib(10)).must.be(55)
    expect(fib(30)).should.be.greater_than(800_000)
    expect(fib(5)).should.not_.be(4)
