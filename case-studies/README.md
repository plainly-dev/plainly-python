# Case study: humanize, rewritten with plainly

`humanize-upstream/` is an untouched clone of https://github.com/python-humanize/humanize (gitignored; re-clone it
with `git clone https://github.com/python-humanize/humanize humanize-upstream`).
`humanize/tests/` is the same behaviour spec rewritten with `plainly`, plus new tests in `test_gaps.py`.

```
pip install -e .. -e "humanize-upstream[tests]"
cd humanize && pytest --plainly      # 118 tests, 783 plain-English checks
```

`humanize/SPEC.md` is that report saved with `--plainly-md SPEC.md`. Commit it with the tests: it is what a reviewer reads instead of the test code, and `git diff SPEC.md` shows promises added or changed as sentences.

## Scope

| Upstream file | Rewritten | Notes |
|---|---|---|
| test_filesize.py, test_lists.py, test_number.py, test_time.py | yes | every upstream row is carried over |
| test_i18n.py | **no** | needs gettext locales and fixtures; `plainly` has nothing for that yet |
| test_benchmarks.py | **no** | performance tests, not behaviour |

## Results (Python 3.12)

- Coverage of `humanize` is the same as upstream's non-i18n tests, and slightly higher: upstream never covered `clamp()`'s invalid-format error.
- Mutation sanity check (6 hand-made bugs): both suites caught 5. Both missed one (`microseconds < 1000` -> `< 999`); `test_gaps.py` now catches it.
- Size: about 1,360 lines against 1,400, because each example now has its own line (`rule.if_(td(days=500)).then_give("1 year, 4 months ago")`). The gain is not length: every check is a sentence, each test is named after the rule it checks, and all 783 checks were carried over identically (compared sentence by sentence).

## Things the rewrite surfaced

- `naturalsize(float("nan"))` raises `ValueError` and `naturalsize(float("inf"))` returns `"inf QB"`, while every other number formatter returns `"NaN"` / `"+Inf"`. Documented in `test_gaps.py`; probably worth an upstream issue.
- `ordinal(-1)` returns `"-1th"`.
- An unknown `minimum_unit` raises a bare `KeyError('BOGUS')`.


# Case study 2: python-semver

`semver-upstream/` is an untouched clone of https://github.com/python-semver/python-semver (gitignored; re-clone it with
`git clone https://github.com/python-semver/python-semver semver-upstream`).
`semver/tests/` is the rewrite, with `semver/SPEC.md` as its committed spec (498 sentences, 63 hand-written wordings to review once).

```
pip install -e .. -e semver-upstream
cd semver && pytest --plainly
```

This one is harder than humanize: it mostly tests **objects and methods** (`Version.parse(x).bump_minor()`), **operators**
(`v1 < v2`), **read-only attributes**, **warnings** and **error messages**, not plain functions.
It pushed four additions into the library:

| Need | Added |
|---|---|
| a method on an object built from the first input | `method(Version.parse, "bump_minor", result=str)` |
| operators and other shapes that don't read as `f(x)` | `spec(f, says="Version({}) < Version({})")`, `name=`, `show=` |
| "this call must warn" | `then_warn(DeprecationWarning, "message")` |
| long values (5,000-digit versions) in sentences | sentences are cut at 100 characters |

`semver/tests/rules.py` holds the small adapters (text in, text out) so each test line stays a single readable rule.

## Scope

Rewritten: parsing, bump (including `next_version`, token validation, digitless builds, issue 484, legacy counters),
compare (including invalid operands and the equality deprecation), match, replace, max/min, format/finalize/repr,
Version object (indexing, immutability, strict parsing, compatibility).
**Not rewritten:** `test_pysemver-cli.py` (runs the command line, so coverage of `cli.py` drops to 17%),
`test_deprecated_functions.py`, `test_docstrings.py`, `test_optional_native_backend.py`, `test_subclass.py`,
`test_typeerror-274.py`, `test_prefixed_example.py`.

## Results (Python 3.12)

- `version.py` coverage is 100%, the same as upstream. Overall coverage is 88% against 100%, entirely from the skipped CLI tests.
- Mutation check (9 hand-made bugs in `version.py`: flipped comparison, bumps off by one, three error messages, the `>=` and `<=` match tables): both suites caught all 9.
- 111 tests, about 1,040 lines against about 1,900 upstream lines for the same files (rules.py included).

## Things the rewrite surfaced

- **Upstream's chained-bump tests never checked the build number.** `v.bump_prerelease().bump_build() == expected` is written with `build.2`,
  but `Version ==` ignores build metadata, and the real result is `build.1` (bumping the prerelease drops the old build).
  Comparing as text exposed it; the rewrite records the true values.


# Case study 3: cachetools

`cachetools-upstream/` is an untouched clone of https://github.com/tkem/cachetools (gitignored; re-clone it with
`git clone https://github.com/tkem/cachetools cachetools-upstream`).
`cachetools/tests/` is the rewrite, with `cachetools/SPEC.md` as its committed spec.

```
pip install -e .. -e cachetools-upstream
cd cachetools && pytest --plainly
```

The hard part here is **state over time**: a cache changes with every call, so a test is a sequence of steps and checks, not an
input and an output. The `if ... then ...` wording does not fit, so the library got a second form, `given(...)`, that reads as a story:

```python
cache = given(LRUCache, maxsize=2)
cache[1] = 1
cache[2] = 2
cache[3] = 3
cache.then.holds_keys(2, 3).lacks(1)
```

```
- given a LRUCache with maxsize=2
- when 1 is set to 1
- and 2 is set to 2
- and 3 is set to 3
- then it holds exactly the keys 2, 3
- and it does not contain 1
```

Every operation really runs on the object; `given` also writes it down. Checks are `then.holds(...)`, `holds_keys(...)`, `contains(...)`,
`lacks(...)`, `has(currsize=2)`, `has_length(n)`, `gave(value)`; expected errors are `with cache.raises(KeyError): ...`.

Upstream shares about 40 rules through a mixin that six test classes inherit. In the rewrite those rules run once per cache class
through a `Cache` fixture, and `SPEC.md` writes each rule once with `⟨each⟩` where the class name goes
(`_Runs for each of: Cache, FIFOCache, LFUCache, ..._`) as long as every run tells the same story. Without that the spec was 4,500 lines.

## Scope

Rewritten: the shared contract (7 cache classes), FIFO, LRU, LFU, random replacement, TTL, most of TLRU, and `keys`.
**Not rewritten:** the decorators (`test_cached.py`, `test_cachedmethod.py`, `test_func.py`, about 2,100 lines) and `test_threading.py`
(they need fake locks and counting, which `plainly` has no wording for yet), and eleven of TLRU's tests
(reverse insert, heap cleanup, datetime, copy, ...).

## Results (Python 3.12)

- 306 tests, `SPEC.md` of about 2,350 lines for 126 stories.
- Coverage of `cachetools/__init__.py` is 97% (upstream 100%). The rest is the decorator code and a few TLRU branches, all from the skipped tests.
- Mutation check (9 hand-made bugs: LRU/FIFO order bookkeeping, six expiry boundaries, an eviction loop): upstream caught all 9. My first
  rewrite caught 8; the survivor (reading a TLRU entry at the exact moment it expires) was covered by a TLRU test I had skipped, so I wrote
  `test_an_entry_read_at_the_exact_moment_it_expires_is_already_gone`, and the rewrite now catches 9.

## Things the rewrite surfaced

- Reading values to check them changes LRU and LFU order (upstream even has a comment warning about it). `holds` therefore exists in two
  forms: `holds_keys(...)` looks only at the keys and never disturbs the order, `holds({...})` reads values and is for order-independent rules.
- Wording shows what a test relies on: "then that gave 1" after `cache[1]` makes it visible that the check itself counts as a *use*.


# Review of the three, and what was fixed

After the three rewrites, two weaknesses stood out: some sentences are wording the author typed (nothing checks that it matches the code),
and some sentences were cut off with `...`, hiding the value that was checked. Both are now visible:

| | humanize | semver | cachetools |
|---|---|---|---|
| Sentences | 783 | 498 | 1,861 |
| Marked `✎` (hand-written wording) | 38 | 378 | 135 |
| Distinct wordings to review once | 38 | 63 | 68 |
| Cut off before | 4 | 8 | 7 |
| Cut off now | 0 | 0 | 0 |

- semver is adapter-heavy (`Version.parse(x).bump_minor()` becomes text in, text out), so 76% of its sentences carry the mark. That is the honest
  price of adapters: the reviewer trusts 63 small wordings instead of reading 498 sentences, but they do have to read those 63.
- The cut-off sentences were fixed three ways: `show=compact` for 5,000-digit versions and googol-sized numbers; a comparison with a label
  ("the copy has the same keys as the source") instead of printing 2,000 numbers; and a module-level class instead of a long `<locals>` name.
