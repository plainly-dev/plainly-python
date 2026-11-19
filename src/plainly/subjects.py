"""What an expectation is *about*: a plain value, or a function call made lazily."""
from __future__ import annotations

import linecache
import re
import sys
import types
from typing import Any, Callable, Optional, Tuple


def _name_of(func: Callable) -> str:
    if getattr(func, "__name__", "") == "<lambda>":
        return "<lambda>"
    return getattr(func, "__qualname__", None) or getattr(func, "__name__", None) or repr(func)


DEFAULT_WIDTH = 100
WIDTH = DEFAULT_WIDTH  # longest a shown value may be before it is cut off (and the spec refuses to be written)
CUT = "…"


def _short(value: Any, limit: Optional[int] = None) -> str:
    limit = limit or WIDTH
    if isinstance(value, types.GeneratorType):
        return "<generator>"
    if isinstance(value, types.FunctionType):
        return value.__name__
    text = repr(value)
    text = re.sub(r" at 0x[0-9a-fA-F]+", "", text)  # memory addresses would make the spec differ on every run
    if not isinstance(value, str):
        text = text.replace("datetime.", "")  # timedelta(days=1) reads better than datetime.timedelta(days=1)
    return text if len(text) <= limit else text[: limit - 1] + CUT


_RUN = re.compile(r"((.{1,4}?)\2{7,})")  # a unit of 1 to 4 characters repeated at least 8 times


def compact(value: Any) -> str:
    """Show a long value without cutting it: ``1<400 × 0>123`` instead of 400 zeros.

    Use it as ``spec(f, show=compact)`` or ``expect(x, show=compact)`` for very long numbers and strings.
    Nothing is lost: the repeat count and the repeated text are both written out.
    """
    text = _short(value, limit=10**9)
    return _RUN.sub(lambda m: f"<{len(m.group(1)) // len(m.group(2))} × {m.group(2)}>", text)


compact._plainly_derived = True  # worked out from the value, not typed by the author


class Value:
    """An already-computed value, optionally labelled with the source that produced it."""

    def __init__(self, value: Any, label: Optional[str] = None, prose: str = "", show: Callable[[Any], str] = _short):
        self.value = value
        self.label = label or show(value)
        self.prose = prose
        self.where = label or "" if prose else ""

    def resolve(self) -> Tuple[Any, Optional[BaseException]]:
        return self.value, None


class Call:
    """A call that has *not* happened yet, so we can check what it raises."""

    def __init__(self, func: Callable, args: tuple, kwargs: dict, show: Callable[[Any], str] = _short):
        self.func, self.args, self.kwargs = func, args, kwargs
        parts = [show(a) for a in args] + [f"{k}={show(v)}" for k, v in kwargs.items()]
        self.arg_texts = [show(a) for a in args]
        self.kwarg_texts = {k: show(v) for k, v in kwargs.items()}
        self.args_label = ", ".join(parts)
        self.name = _name_of(func)
        self.label = f"{self.name}({self.args_label})"
        self._outcome: Optional[Tuple[Any, Optional[BaseException]]] = None
        self.prose = ""
        self.where = ""

    def resolve(self) -> Tuple[Any, Optional[BaseException]]:
        """Run the call once and remember what happened (so side effects never repeat)."""
        if self._outcome is None:
            try:
                self._outcome = (self.func(*self.args, **self.kwargs), None)
            except Exception as exc:  # noqa: BLE001 - we want to inspect any error
                self._outcome = (None, exc)
        return self._outcome


def source_label(depth: int = 2) -> Optional[str]:
    """Best effort: recover the text inside ``expect(...)`` from the caller's source line."""
    try:
        frame = sys._getframe(depth)
        lines = []
        for offset in range(8):  # allow the call to span a few lines
            line = linecache.getline(frame.f_code.co_filename, frame.f_lineno + offset)
            if not line:
                break
            lines.append(line.strip())
            text = " ".join(lines)
            start = text.find("expect(")
            if start == -1:
                return None
            level, begin = 0, start + len("expect(")
            for i in range(begin - 1, len(text)):
                if text[i] == "(":
                    level += 1
                elif text[i] == ")":
                    level -= 1
                    if level == 0:
                        inner = text[begin:i].strip()
                        return inner or None
        return None
    except Exception:  # noqa: BLE001
        return None
