# CRM contacts, tests first (no app yet)

This folder holds the tests for a small Flask CRM, written with `plainly` **before any app code exists**.
The point is to see how well plainly works as the contract a person reviews before anything gets built.

- `tests/CONTRACT.md`: what the app must do, in prose (routes, field rules, error answers).
- `tests/test_*.py`: 53 tests, every check a plainly sentence (`plainly-lint tests/` passes).
- `tests/crm.py`: the only helper. One method per HTTP request; it keeps `status`, `body`, `error`, `errors`,
  `names`, `texts`, `location` and `page` from the last answer. **Read it once**: those names are chosen by hand.
- `SPEC.md`: the generated spec, 53 stories. Review this file instead of the test code.
- `FEEDBACK.md`: what plainly was missing while writing these tests.

The app (`crm_app/`, with `create_app()`) is Trello card 11 and is not here yet, so today every test fails with
`ModuleNotFoundError: No module named 'crm_app'`. That is expected. The tests are not run by the root CI suite.

```
pip install flask -e ../..      # from case-studies/crm
pytest                          # red until crm_app exists
pytest --plainly-md SPEC.md     # only rewrites SPEC.md on a passing run
```

## How SPEC.md was produced before the app existed

plainly only writes `SPEC.md` from a passing run. To get one, and to check that the tests do not contradict each other,
the tests were run once against a throwaway reference app kept outside the repository. It was deleted afterwards and
is not committed, so whoever builds `crm_app/` starts from the contract and the tests alone.
