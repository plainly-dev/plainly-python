"""Rules that read aloud as sentences.

    rule = spec(ordinal)
    rule.if_("11").then_give("11th")      # "ordinal: if '11', then give '11th'"
    rule.if_(None).then_raise(TypeError)  # "ordinal: if None, then raise TypeError"

Three options adapt the wording to other shapes of code:

    spec(f, name="...")    # call the function something else in the sentence (lambdas, operators)
    spec(f, says="{} < {}")  # write the whole condition yourself; {} are the shown inputs
    spec(f, show=str)      # render values with str() instead of repr()
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

from .expectation import Expectation
from .subjects import Call, _short


class RuleExpectation(Expectation):
    """An Expectation that words itself as "<function>: if <inputs>, then give <result>"."""

    def __init__(self, subject, modal="should", negated=False, says=None, show=_short):
        super().__init__(subject, modal, negated)
        self._says, self._show = says, show

    def _with(self, **changes) -> "RuleExpectation":
        data = dict(modal=self._modal, negated=self._negated)
        data.update(changes)
        return RuleExpectation(self._subject, says=self._says, show=self._show, **data)

    def _sentence(self, phrase: str) -> str:
        verb, _, rest = phrase.partition(" ")
        verb = "give" if verb == "return" else verb
        must = "must " if self._modal == "must" else ""
        no = "not " if self._negated else ""
        subject = self._subject
        if self._says:
            return f"if {self._says.format(*subject.arg_texts, **subject.kwarg_texts)}, then {must}{no}{verb} {rest}".rstrip()
        inputs = subject.args_label or "called with nothing"
        return f"{subject.name}: if {inputs}, then {must}{no}{verb} {rest}".rstrip()


class Case:
    """One example: the inputs after ``if_``, the outcome after ``then_``."""

    def __init__(self, func, modal, positional, keyword, name=None, says=None, show=_short):
        call = Call(func, positional, keyword, show)
        reasons, where = [], []
        if name:
            call.name = name
            reasons.append("name")
            where.append(f'name "{name}"')
        if says:
            reasons.append("says")
            where.append(f'says "{says}"')
        if show is not _short and not getattr(show, "_plainly_derived", False):
            reasons.append("show")
        adapter = getattr(func, "_plainly_adapter", None)
        if adapter or getattr(func, "__name__", "") == "<lambda>":
            reasons.append("adapter")
            if isinstance(adapter, str):
                where.append(f"method adapter {adapter}")
            else:
                code = getattr(func, "__code__", None)
                where.append(f"lambda at {os.path.basename(code.co_filename)}:{code.co_firstlineno}" if code else "lambda")
        call.prose = ", ".join(reasons)
        call.where = "; ".join(where)
        self._e = RuleExpectation(call, modal, says=says, show=show)

    def then_give(self, expected: Any) -> "Case":
        self._e.return_(expected)
        return self

    def then_raise(self, exception: Any = Exception, message: Any = None) -> "Case":
        self._e.raise_(exception, message)
        return self

    def then_warn(self, category: Any = Warning, message: Any = None) -> "Case":
        """Check for a warning. Put it before ``then_give``: the call runs once, under the warning check."""
        self._e.warn_(category, message)
        return self

    def then_not_raise(self) -> "Case":
        self._e.not_.raise_(Exception)
        return self


class Spec:
    """Holds the function under test. Each ``if_`` starts one example."""

    def __init__(self, func: Callable, modal: str = "should", name=None, says=None, show=_short):
        self._func, self._modal, self._name, self._says, self._show = func, modal, name, says, show

    def if_(self, *positional: Any, **keyword: Any) -> Case:
        return Case(self._func, self._modal, positional, keyword, self._name, self._says, self._show)

    @property
    def must(self) -> "Spec":
        """Use for non-negotiable rules: ``spec(f).must.if_(1).then_give(2)``."""
        return Spec(self._func, "must", self._name, self._says, self._show)


def spec(func: Callable, *, name: Optional[str] = None, says: Optional[str] = None,
         show: Callable[[Any], str] = _short) -> Spec:
    return Spec(func, name=name, says=says, show=show)


def method(factory: Callable, name: str, result: Optional[Callable] = None) -> Callable:
    """Turn "build an object from the first input, then call one of its methods" into a plain function.

        bump_minor = spec(method(Version.parse, "bump_minor", result=str))
        bump_minor.if_("3.4.5").then_give("3.5.0")   # bump_minor: if '3.4.5', then give '3.5.0'
    """

    def run(subject, *args, **kwargs):
        value = getattr(factory(subject), name)(*args, **kwargs)
        return result(value) if result else value

    run.__name__ = run.__qualname__ = name
    run._plainly_adapter = f"{getattr(factory, '__qualname__', factory)}().{name}"
    return run
