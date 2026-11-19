# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) maintaining or contributing to this repository.
Humans: see [CONTRIBUTING.md](CONTRIBUTING.md), which follows the same rules.

## What this project is

`plainly` is a pytest plugin and assertion library for Python. It turns each test check into one plain-English sentence
(`fib(-1) should raise ValueError`), so a person can review AI-written tests by reading a list of promises instead of test code.
It also writes those sentences to a `SPEC.md` file and reports pull requests that remove or loosen a promise (`plainly-diff`).

No runtime dependencies. Python 3.9+. MIT license.

## Layout

| Path | What it holds |
|---|---|
| `src/plainly/expectation.py` | `expect(...)` and `calling(...)`, the `should` / `must` checks |
| `src/plainly/spec.py` | `spec(f).if_(x).then_give(y)` rules for one function, `method(...)` adapter |
| `src/plainly/story.py` | `given(Class, ...)` step-by-step stories for objects that change over time |
| `src/plainly/subjects.py` | how values and calls are written in sentences (`compact`, labels) |
| `src/plainly/recorder.py` | collects sentences while tests run |
| `src/plainly/pytest_plugin.py` | `--plainly`, `--plainly-md`, `--plainly-check`, `--plainly-width` |
| `src/plainly/diff.py` | the `plainly-diff` command (compares `SPEC.md` across git revisions) |
| `tests/` | the library's own tests |
| `examples/` | a small demo and `spec-review.yml`, a workflow that posts `plainly-diff` on PRs |
| `case-studies/` | real libraries' test suites rewritten with plainly; each has a committed `SPEC.md` |

## Commands

```bash
pip install -e ".[dev]"          # install with pytest
pytest                           # run the library tests and examples
pytest --plainly                 # same, and print every check as a sentence
plainly-diff --base origin/main SPEC.md   # what a change promises less of
```

CI (`.github/workflows/ci.yml`) runs `pytest --plainly` on Python 3.9 to 3.14. All six jobs must pass before a PR can merge.

## Rules

1. **Keep it dependency-free.** Only the standard library at runtime; pytest is the only dev dependency.
   Code must run on Python 3.9, so no `match` statements and no `X | Y` type unions at runtime.
2. **Sentences are the product.** Any change to how a sentence is worded changes every user's `SPEC.md`.
   Treat wording changes as breaking: say so in the PR description and update `README.md` examples to match.
3. **Never cut a value silently.** Sentences longer than the width limit must fail loudly, as they do now.
4. **Tests.** Every behaviour change gets a test in `tests/`. Tests of plainly's own internals may use plain `assert`
   (testing the assertion library with itself would be circular). Examples and case studies must use plainly sentences only.
5. **Case studies.** If you change sentence output, regenerate the affected spec and commit it:
   `cd case-studies/<name> && pytest --plainly-md SPEC.md`. Do not edit a `SPEC.md` by hand.
   The `*-upstream/` folders are gitignored clones; never commit them.
6. **One change per pull request.** `main` is protected: open a PR from a branch, never push to `main`.
   Write the PR description as what the change promises, in plain sentences, the same way plainly does.
7. **Don't weaken a promise quietly.** If a change removes or loosens a check, `plainly-diff --fail-on-weakened`
   will flag it. Explain why in the PR description.

## Using plainly in other projects

If you are an agent writing tests for a *different* project with plainly, write each check as one sentence:

```python
from plainly import expect, calling, spec, given

expect(total([3, 5])).should.be(8)
calling(parse, "").should.raise_(ValueError, message="empty")
spec(ordinal).if_(11).then_give("11th")
```

Prefer `spec(...)` for many examples of one function and `given(...)` for objects that change over time.
Avoid bare `assert` and `pytest.raises`, then run `pytest --plainly-md SPEC.md` and commit `SPEC.md` with the tests.
