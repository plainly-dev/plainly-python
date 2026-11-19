"""plainly: tests that read like plain English.

    from plainly import expect, calling

    expect(sum_(3, 5)).should.be(8)
    calling(fib, -1).should.raise_(ValueError)
"""
from .expectation import Be, Expectation, PlainlyError, calling, expect
from .spec import Spec, method, spec
from .story import Story, given
from .subjects import compact

__all__ = ["expect", "calling", "spec", "method", "Spec", "given", "Story", "compact", "Expectation", "Be", "PlainlyError"]
__version__ = "0.1.0"
