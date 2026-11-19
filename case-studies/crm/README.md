# CRM contacts page, built test-first by two agents

1. **Test-writer agent** wrote `tests/` (113 tests, `tests/CONTRACT.md`) with no app code in existence, using `plainly`.
2. The tests were checked red (all 113 failed with `No module named 'crm_app'`), then locked: read-only folder plus a checksum.
3. **Implementer agent** wrote `crm_app/` seeing only the tests. It could not change them.
4. Checked afterwards: 113 pass, test checksums identical, 99% coverage, no special-casing of test inputs,
   and the implementer's transcript shows it read only `tests/` (4 commands, none outside the project).

`SPEC.md` is the generated spec (114 stories, 833 sentences, no hand-written wording marks).
`NOTES_FROM_IMPLEMENTER.md` lists the five places the implementer had to guess.

```
pip install flask -e ../..      # from case-studies/crm
pytest
pytest --plainly-md SPEC.md
```

## How good were the tests? (18 deliberate bugs put into the finished app)

First run: 16 caught, 2 survived. After the follow-up below: 17 caught, 1 left (by design).

- **Duplicate email check made case-sensitive: survived the first run.** A real gap. The tests only registered a lowercase email and retried it in capitals.
  Fixed by `test_an_email_saved_with_capitals_still_blocks_the_lowercase_version` (register `Ann@Example.com`, retry `ann@example.com`).
  Three variants of the bug were tried; the new test fails on all three, and the app needed no change (114 tests pass).
- Deleted ids reused: survived, and that is by design. The contract leaves it open, so it is not a bug.

Caught: search ignoring company, case-sensitive search, edit clashing with your own email, notes oldest first, name limit off by one,
no trimming, unescaped name (XSS), refused create answering 200, pipeline count wrong, delete doing nothing, any text accepted as an email,
status filter ignored, unknown API id answering HTML, whitespace-only note accepted, unknown contact not 404, edit skipping validation.
