# plainly

Unit-test assertions that read like English, so a human can review AI-written tests in seconds.

AI can write hundreds of tests an hour. Reviewing them is the bottleneck: noisy setup,
`assert` soup, and mock plumbing bury the one thing the reviewer cares about:
**what behaviour is being promised?** `plainly` makes every check a single readable sentence.

```python
from plainly import expect, calling

calling(fib, -1).should.raise_(ValueError)
calling(fib, 2.5).should.raise_(ValueError)
expect(fib(2)).must.be(1)
expect(sum(3, 5)).should.be(8)
expect(fib(30)).should.be.greater_than(800_000)
```

## The review report

```
pytest --plainly
```

```
fib(-1) should raise ValueError
fib(2.5) should raise ValueError
fib(2) must be 1
sum(3, 5) should be 8
```

A reviewer can read this list without opening the test code, and ask one question: *is this the right spec?*
Failures read the same way:

```
sum(3, 5) should be 9
  but it was 8
```

## Many examples of one function

Write each example so it reads aloud as "if this, then that":

```python
rule = spec(ordinal)

def test_teens_always_take_th():
    rule.if_("11").then_give("11th")
    rule.if_("12").then_give("12th")

def test_something_that_is_not_a_number_is_left_alone():
    rule.if_("something else").then_give("something else")
    rule.if_(None).then_raise(TypeError)
```

The report says the same thing:

```
ordinal: if '11', then give '11th'
ordinal: if '12', then give '12th'
ordinal: if None, then raise TypeError
```

Strings keep their quotes, so `if 11` (a number) and `if '11'` (text) never look alike. Keywords work too: `rule.if_(3000, gnu=True).then_give("2.9K")`.
(`if_` has a trailing underscore because `if` is a Python keyword, like `raise_` and `return_`.)
Use `spec(f).must.if_(...)` for non-negotiable rules: "then must give".

Other outcomes and adapters:

| You write | Reads as |
|---|---|
| `rule.if_(x).then_raise(ValueError, "negative")` | if x, then raise ValueError with message containing 'negative' |
| `rule.if_(x).then_warn(DeprecationWarning).then_give(y)` | if x, then warn DeprecationWarning ... then give y |
| `spec(f, says="Version({}) < Version({})")` | write the whole condition yourself |
| `spec(f, name="parse")` / `spec(f, show=str)` | rename the function / render values with `str()` |
| `spec(method(Version.parse, "bump_minor", result=str))` | test a method of an object built from the first input |

## Objects that change over time

When a test is a sequence of steps, write it as a story. Every operation really runs, and is also written down:

```python
cache = given(LRUCache, maxsize=2)       # given a LRUCache with maxsize=2
cache[1] = 1                             # when 1 is set to 1
cache[2] = 2                             # and 2 is set to 2
cache[3] = 3                             # and 3 is set to 3
cache.then.holds_keys(2, 3).lacks(1)     # then it holds exactly the keys 2, 3 / and it does not contain 1

with cache.raises(ValueError):           # when 4 is set to 4 / then that raises ValueError
    cache[4] = 4
```

Checks: `then.holds({...})`, `holds_keys(...)`, `holds_nothing()`, `contains(...)`, `lacks(...)`, `has(currsize=2)`,
`has_length(n)`, `contains_one_of(...)`, `gave(value)`. A method call is written as `update({1: 1}) is called`, with `giving ...` when it returns something.

## Reviewing in git

The code diff of a test file is noisy. Commit the spec next to the tests, and reviewers read that instead:

```
pytest --plainly-md SPEC.md      # regenerate the spec; commit it with your tests
pytest --plainly-check SPEC.md   # in CI: fails if SPEC.md is out of date
```

A PR then shows exactly which promises changed:

```diff
 ### Joins with commas and a final and
 - natural_list: if ['a', 'b', 'c', 'd'], then give 'a, b, c and d'
+- natural_list: if ['x', 'y', 'z'], then give 'x, y and z'
+
+### None is written as the word none
+
+- natural_list: if ['a', None], then give 'a and None'
```

Failing runs never rewrite the spec, and memory addresses are stripped so the file only changes when behaviour does.
A test that runs once per parameter is written once, with `⟨each⟩`, when every run tells the same story.

## Reviewing a pull request: what does it promise less of?

```
plainly-diff --base origin/main SPEC.md                      # Markdown report, ready for a PR comment
plainly-diff --base origin/main SPEC.md --fail-on-weakened   # exit 1 if a check was removed or made looser
```

It reads the `SPEC.md` on the base branch and the one in your working tree and sorts every difference:

| Reported as | Meaning | Fails `--fail-on-weakened`? |
|---|---|---|
| ⚠️ Removed check / removed story | a promise disappeared (a renamed story is not a removal) | yes |
| ⚠️ Check made looser | same situation, weaker outcome: the error message is no longer checked, `raise ValueError` became `raise Exception`, or a value became an error | yes |
| Expectation changed | same situation, different outcome: shown as before / now | no, but a human should look |
| ✎ New hand-written wording | new wording the author typed, to check against the code | no |
| Added | new checks and stories, collapsed | no |

Example, from a pull request that quietly dropped one example, deleted one test, loosened one error check and added a label:

```
**1 check removed, 1 story removed, 1 check made looser, 1 new hand-written wording, 1 check added, 1 story added.**
⚠️ This change promises less than before. Please confirm each removal below is intended.

### ⚠️ Removed checks
- `tests/test_number.py` › **Ordinal teens always take th**
  - `ordinal: if '12', then give '12th'`
### ⚠️ Checks made looser
  - before: `clamp: if 5, format=3, then raise ValueError with message containing 'Invalid format'`
  - now: `clamp: if 5, format=3, then raise Exception` — no longer checks the error message
```

A ready-made GitHub workflow that posts this comment is in [`examples/spec-review.yml`](examples/spec-review.yml).

## What a reviewer still has to check

The sentences in `SPEC.md` are built from the real call, so they can be trusted. Wording the test author typed by hand cannot, so it is marked:

- A `✎` at the end of a sentence means its wording is hand-written: an `expect(x, "label")`, `says=`, `name=`, `described_as=`, an adapter (a lambda or `method(...)`) or a custom `show=`.
- The top of `SPEC.md` lists each hand-written wording **once**, with where it is defined and how many sentences use it
  (`says "Version({}) < Version({})"; lambda at rules.py:34 (6 sentences)`), so a reviewer checks 63 wordings instead of 378 sentences.
- A value that does not fit in a sentence is **never silently cut**. Past 100 characters `plainly` refuses to write the spec and names the sentences.
  Show the value another way: `show=compact` writes `1<400 × 0>123` for 400 zeros, a smaller example, a label, or `--plainly-width N`.

## For AI agents

`plainly` is built for tests written by AI coding agents. If you are an agent:

- **Writing tests with plainly in another project:** write every check as one sentence (`expect`, `calling`, `spec`, `given`),
  avoid bare `assert` and `pytest.raises`, then run `pytest --plainly-md SPEC.md` and commit `SPEC.md` with the tests.
- **Contributing to plainly itself:** read [AGENTS.md](AGENTS.md) for the layout, commands and rules.
- A short machine-readable summary of the project is in [llms.txt](llms.txt).

## Install (from source for now)

```
pip install -e ".[dev]"
pytest --plainly
```

Works with plain pytest (assertions raise `AssertionError`). No dependencies. Python 3.9+.

## API

| You write | Reads as |
|---|---|
| `expect(x).should.be(8)` | x should be 8 |
| `expect(x).must.not_.be(8)` | x must not be 8 |
| `calling(f, a, b).should.raise_(ValueError)` | f(a, b) should raise ValueError |
| `calling(f).should.raise_(ValueError, message="bad")` | ...with message containing 'bad' |
| `calling(f, a).should.return_(3)` | f(a) should return 3 |
| `expect(x).should.be.greater_than(3)` | also `less_than`, `at_least`, `at_most`, `between`, `close_to`, `none`, `true`, `false`, `empty`, `instance_of`, `one_of` |
| `expect(x).should.contain(i)` / `have_length(n)` / `start_with` / `end_with` / `match(regex)` | |
| `expect(x).should.satisfy(pred, "is even")` | escape hatch: the description is what the reviewer reads |

`should` and `must` are interchangeable wording: use `must` for rules that are non-negotiable.

### Why `calling(fib, -1)` and not `fib(-1).should.raise(...)`?

In Python, `fib(-1)` runs *before* `.should` can see it, so the exception escapes the test.
`calling(...)` defers the call. Also, `raise` and `return` are reserved words, so the
matchers are `raise_` / `return_` (aliases `raises`, `returns`, `give`).

### Labels

`expect(sum(3, 5))` labels the sentence with the source text `sum(3, 5)`. If the source can't be
read (REPL, `exec`), it falls back to `repr(value)`. Override with `expect(value, "label")`.

## Roadmap ideas

- Table-style cases (`fib` with `0 -> 0, 1 -> 1, ...`) rendered as a grid
- `--plainly` output to Markdown for PR comments
- Lint rule/AI prompt: "write tests only using plainly sentences"
- Spying/mocks phrased as sentences (`mailer should have been called with ...`)
- Same sentence model for other languages

## License

MIT
