"""Given / when / then stories for objects that change over time.

    cache = given(LRUCache, maxsize=2)       # given an LRUCache with maxsize=2
    cache[1] = "a"                           # when 1 is set to 'a'
    cache[2] = "b"                           # and 2 is set to 'b'
    cache[3] = "c"                           # and 3 is set to 'c'
    cache.then.holds({2: "b", 3: "c"})       # then it holds exactly {2: 'b', 3: 'c'}

Every operation you run on the wrapped object happens for real and is also written down as a sentence,
so the spec shows the whole story and not just the final check.
"""
from __future__ import annotations

import inspect
from contextlib import contextmanager
from typing import Any, Callable

from . import recorder
from .expectation import PlainlyError
from .subjects import _short


def _words(name: str) -> str:
    return name.replace("_", " ")


class Caught:
    value: BaseException | None = None


class Story:
    def __init__(self, target: Any, description: str, show: Callable[[Any], str] = _short, prose: str = ""):
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_show", show)
        object.__setattr__(self, "_last", None)
        object.__setattr__(self, "_stage", "given")
        recorder.add(f"given {description}", True, prose, description if prose else "")

    # ----- recording ---------------------------------------------------------------
    def _say(self, stage: str, sentence: str, ok: bool = True) -> None:
        connector = stage if self._stage != stage else "and"
        object.__setattr__(self, "_stage", stage)
        recorder.add(f"{connector} {sentence}", ok)

    def _remember(self, result: Any) -> None:
        object.__setattr__(self, "_last", result)

    # ----- operations on the wrapped object -------------------------------------
    def __setitem__(self, key, value):
        self._say("when", f"{self._show(key)} is set to {self._show(value)}")
        self._target[key] = value

    def __getitem__(self, key):
        result = self._target[key]
        self._say("when", f"{self._show(key)} is read, giving {self._show(result)}")
        self._remember(result)
        return result

    def __delitem__(self, key):
        self._say("when", f"{self._show(key)} is deleted")
        del self._target[key]

    def __contains__(self, key):
        return key in self._target

    def __len__(self):
        return len(self._target)

    def __iter__(self):
        return iter(self._target)

    def __repr__(self):
        return repr(self._target)

    def __getattr__(self, name):
        value = getattr(self._target, name)
        if inspect.ismethod(value) or inspect.isbuiltin(value) or inspect.isfunction(value):
            def call(*args, **kwargs):
                shown = [self._show(a) for a in args] + [f"{k}={self._show(v)}" for k, v in kwargs.items()]
                self._say("when", f"{name}({', '.join(shown)}) is called")
                result = value(*args, **kwargs)
                if result is self._target:  # a fluent method: keep the story going, so a check can follow on the same line
                    self._remember(None)
                    return self
                if result is not None:
                    recorder.add(f"  giving {self._show(result)}", True)
                self._remember(result)
                return result

            return call
        return value

    def unwrap(self) -> Any:
        """The real object, for when you need to hand it to other code."""
        return self._target

    # ----- expected errors -----------------------------------------------------
    @contextmanager
    def raises(self, exception: type, message: str | None = None):
        """``with cache.raises(KeyError) as error: del cache[1]`` -> "then that raises KeyError".

        ``error.value`` is the exception, for any extra checks.
        """
        caught = Caught()
        try:
            yield caught
        except exception as exc:
            caught.value = exc
            if message is not None and message not in str(exc):
                self._say("then", f"that raises {exception.__name__} with message containing {self._show(message)}", False)
                raise PlainlyError(f"expected the message to contain {message!r} but it was {str(exc)!r}") from exc
            suffix = f" with message containing {self._show(message)}" if message else ""
            self._say("then", f"that raises {exception.__name__}{suffix}")
            return
        except Exception as exc:  # noqa: BLE001
            self._say("then", f"that raises {exception.__name__}", False)
            raise PlainlyError(f"expected {exception.__name__} but it raised {type(exc).__name__}: {exc}") from exc
        self._say("then", f"that raises {exception.__name__}", False)
        raise PlainlyError(f"expected {exception.__name__} but nothing was raised")

    @property
    def then(self) -> "Then":
        return Then(self)


class Then:
    def __init__(self, story: Story):
        self._story = story

    def _check(self, sentence: str, ok: bool, actual: str) -> "Then":
        self._story._say("then", sentence, ok)
        if not ok:
            raise PlainlyError(f"then {sentence}\n  but {actual}")
        return self

    @property
    def _show(self):
        return self._story._show

    def holds(self, expected: dict) -> "Then":
        actual = dict(self._story._target.items())
        return self._check(f"it holds exactly {self._show(expected)}", actual == expected, f"it held {self._show(actual)}")

    def holds_keys(self, *keys: Any) -> "Then":
        """Exactly these keys, in this order. Reads no values, so it never changes LRU or LFU order."""
        actual = list(self._story._target)
        shown = ", ".join(self._show(k) for k in keys)
        return self._check(f"it holds exactly the keys {shown}", actual == list(keys), f"it held the keys {self._show(actual)}")

    def holds_nothing(self) -> "Then":
        actual = dict(self._story._target.items())
        return self._check("it is empty", not actual, f"it held {self._show(actual)}")

    def contains(self, *keys: Any) -> "Then":
        missing = [k for k in keys if k not in self._story._target]
        return self._check(
            "it contains " + ", ".join(self._show(k) for k in keys), not missing, f"it was missing {self._show(missing)}"
        )

    def lacks(self, *keys: Any) -> "Then":
        present = [k for k in keys if k in self._story._target]
        return self._check(
            "it does not contain " + ", ".join(self._show(k) for k in keys), not present, f"it still contained {self._show(present)}"
        )

    def has_length(self, n: int) -> "Then":
        actual = len(self._story._target)
        return self._check(f"it has {n} {'entry' if n == 1 else 'entries'}", actual == n, f"it had {actual}")

    def contains_one_of(self, *keys: Any) -> "Then":
        found = [k for k in keys if k in self._story._target]
        return self._check(
            "it contains at least one of " + ", ".join(self._show(k) for k in keys), bool(found), "it contained none of them"
        )

    def has(self, **attributes: Any) -> "Then":
        actual = {name: getattr(self._story._target, name) for name in attributes}
        text = ", ".join(f"{_words(n)} {self._show(v)}" for n, v in attributes.items())
        return self._check(f"it has {text}", actual == attributes, f"it had {self._show(actual)}")

    def gave(self, expected: Any) -> "Then":
        actual = self._story._last
        return self._check(f"that gave {self._show(expected)}", actual == expected, f"it gave {self._show(actual)}")


def given(factory: Any, *args: Any, show: Callable[[Any], str] = _short, described_as: str | None = None, **kwargs: Any) -> Story:
    """Start a story with a new object (``given(LRUCache, maxsize=2)``) or an existing one."""
    if callable(factory) and (args or kwargs or isinstance(factory, type)):
        target = factory(*args, **kwargs)
        name = getattr(factory, "__name__", repr(factory))
        parts = [show(a) for a in args] + [f"{k}={show(v)}" for k, v in kwargs.items()]
        description = f"a {name}" + (f" with {', '.join(parts)}" if parts else "")
    else:
        target, description = factory, f"{type(factory).__name__} {show(factory)}"
    return Story(target, described_as or description, show, "described_as" if described_as else "")
