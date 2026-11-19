"""The fluent, English-reading API: ``expect(x).should.be(8)``."""
from __future__ import annotations

import math
import re
import warnings
from typing import Any, Callable, Optional, Union

from . import recorder
from .subjects import Call, Value, _short, source_label


class PlainlyError(AssertionError):
    """Raised when an expectation is not met. The message is a readable sentence."""


def _type_name(t: Any) -> str:
    return t.__name__ if isinstance(t, type) else _short(t)


class Expectation:
    def __init__(self, subject: Union[Value, Call], modal: str = "should", negated: bool = False):
        self._subject = subject
        self._modal = modal
        self._negated = negated
        self._show = _short

    # ----- grammar ---------------------------------------------------------
    def _with(self, **changes) -> "Expectation":
        data = dict(modal=self._modal, negated=self._negated)
        data.update(changes)
        copy = Expectation(self._subject, **data)
        copy._show = self._show
        return copy

    @property
    def should(self) -> "Expectation":
        return self._with(modal="should")

    @property
    def must(self) -> "Expectation":
        return self._with(modal="must")

    @property
    def not_(self) -> "Expectation":
        return self._with(negated=not self._negated)

    @property
    def be(self) -> "Be":
        return Be(self)

    # ----- internals -------------------------------------------------------
    def _sentence(self, phrase: str) -> str:
        neg = " not" if self._negated else ""
        return f"{self._subject.label} {self._modal}{neg} {phrase}"

    def _finish(self, phrase: str, ok: bool, actual: str) -> "Expectation":
        sentence = self._sentence(phrase)
        recorder.add(sentence, ok, getattr(self._subject, "prose", ""), getattr(self._subject, "where", ""))
        if not ok:
            raise PlainlyError(f"{sentence}\n  but {actual}")
        return self

    def _check_value(self, phrase: str, test: Callable[[Any], bool], describe: Optional[Callable[[Any], str]] = None):
        value, exc = self._subject.resolve()
        if exc is not None:
            return self._finish(phrase, False, f"it raised {type(exc).__name__}: {exc}")
        ok = bool(test(value))
        if self._negated:
            ok = not ok
        actual = describe(value) if describe else f"it was {self._show(value)}"
        return self._finish(phrase, ok, actual)

    # ----- matchers --------------------------------------------------------
    def equal(self, expected: Any) -> "Expectation":
        return self._check_value(f"equal {_short(expected)}", lambda v: v == expected)

    def return_(self, expected: Any) -> "Expectation":
        return self._check_value(f"return {self._show(expected)}", lambda v: v == expected)

    returns = give = return_

    def contain(self, item: Any) -> "Expectation":
        return self._check_value(f"contain {_short(item)}", lambda v: item in v)

    def have_length(self, n: int) -> "Expectation":
        return self._check_value(f"have length {n}", lambda v: len(v) == n,
                                 lambda v: f"its length was {len(v)}")

    def start_with(self, prefix: str) -> "Expectation":
        return self._check_value(f"start with {_short(prefix)}", lambda v: v.startswith(prefix))

    def end_with(self, suffix: str) -> "Expectation":
        return self._check_value(f"end with {_short(suffix)}", lambda v: v.endswith(suffix))

    def match(self, pattern: str) -> "Expectation":
        return self._check_value(f"match /{pattern}/", lambda v: re.search(pattern, v) is not None)

    def satisfy(self, predicate: Callable[[Any], bool], description: str) -> "Expectation":
        """Escape hatch. ``description`` is what reviewers read, so keep it honest."""
        return self._check_value(f"satisfy: {description}", predicate)

    def raise_(self, exception: type = Exception, message: Optional[str] = None) -> "Expectation":
        """Check that the call raises. ``exception`` may be a class or its name as a string."""
        if not isinstance(self._subject, Call):
            raise TypeError("raise_() needs a call that has not run yet: use calling(func, *args), not expect(value)")
        name = exception if isinstance(exception, str) else exception.__name__
        phrase = f"raise {name}" + (f" with message containing {self._show(message)}" if message else "")
        _, exc = self._subject.resolve()

        def type_matches(e: BaseException) -> bool:
            return any(c.__name__ == name for c in type(e).__mro__) if isinstance(exception, str) \
                else isinstance(e, exception)

        raised = exc is not None and type_matches(exc) and (message is None or message in str(exc))
        ok = (not raised) if self._negated else raised
        if exc is None:
            actual = f"it returned {self._show(self._subject.resolve()[0])} without raising"
        else:
            actual = f"it raised {type(exc).__name__}: {exc}"
        return self._finish(phrase, ok, actual)

    raises = raise_

    def warn_(self, category: type = Warning, message: Optional[str] = None) -> "Expectation":
        """Check that the call issues a warning (run first: the call is only run once)."""
        if not isinstance(self._subject, Call):
            raise TypeError("warn_() needs a call that has not run yet: use calling(func, *args), not expect(value)")
        phrase = f"warn {category.__name__}" + (f" with message containing {self._show(message)}" if message else "")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._subject.resolve()
        matching = [w for w in caught if issubclass(w.category, category) and (message is None or message in str(w.message))]
        ok = (not matching) if self._negated else bool(matching)
        if caught:
            actual = "it warned " + "; ".join(f"{w.category.__name__}: {w.message}" for w in caught)
        else:
            actual = "it issued no warning"
        return self._finish(phrase, ok, actual)

    warns = warn_


class Be:
    """``expect(x).should.be(8)`` and ``expect(x).should.be.greater_than(3)`` both work."""

    def __init__(self, e: Expectation):
        self._e = e

    def __call__(self, expected: Any) -> Expectation:
        return self._e._check_value(f"be {self._e._show(expected)}", lambda v: v == expected)

    def none(self):
        return self._e._check_value("be None", lambda v: v is None)

    def true(self):
        return self._e._check_value("be True", lambda v: v is True)

    def false(self):
        return self._e._check_value("be False", lambda v: v is False)

    def truthy(self):
        return self._e._check_value("be truthy", bool)

    def falsy(self):
        return self._e._check_value("be falsy", lambda v: not v)

    def empty(self):
        return self._e._check_value("be empty", lambda v: len(v) == 0)

    def greater_than(self, n):
        return self._e._check_value(f"be greater than {n}", lambda v: v > n)

    def less_than(self, n):
        return self._e._check_value(f"be less than {n}", lambda v: v < n)

    def at_least(self, n):
        return self._e._check_value(f"be at least {n}", lambda v: v >= n)

    def at_most(self, n):
        return self._e._check_value(f"be at most {n}", lambda v: v <= n)

    def between(self, low, high):
        return self._e._check_value(f"be between {low} and {high}", lambda v: low <= v <= high)

    def close_to(self, expected: float, tolerance: float = 1e-9):
        return self._e._check_value(f"be close to {expected} (±{tolerance})",
                                    lambda v: math.isclose(v, expected, abs_tol=tolerance, rel_tol=0))

    def instance_of(self, t: type):
        return self._e._check_value(f"be an instance of {_type_name(t)}", lambda v: isinstance(v, t),
                                    lambda v: f"it was a {type(v).__name__}: {_short(v)}")

    def one_of(self, *options):
        return self._e._check_value(f"be one of {list(options)}", lambda v: v in options)


# ----- entry points --------------------------------------------------------
def expect(value: Any, label: Optional[str] = None, show: Callable[[Any], str] = _short) -> Expectation:
    """Start a check about a value. The label defaults to the source text you wrote."""
    expectation = Expectation(Value(value, label or source_label(), prose="label" if label else "", show=show))
    expectation._show = show
    return expectation


def calling(func: Callable, *args: Any, **kwargs: Any) -> Expectation:
    """Start a check about a call that runs lazily, so errors can be asserted."""
    return Expectation(Call(func, args, kwargs))
