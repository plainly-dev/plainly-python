# What plainly was missing while writing these tests

Written while designing `tests/` for an HTTP app with no code behind it yet (Trello card 10).
Each point says what happened and what would help. Nothing here is fixed yet.

## Worked well

- `given(CRM)` stories read as a real session: `when post('/api/contacts', ...) is called` / `then it has status 409, error 'email already exists'`.
  Every request is in the spec, so a reviewer sees the setup and not only the check.
- `spec(add_contact).if_(...).then_give((400, {...}))` turned the field rules into one line per example, with no hand-written wording.
- Long values failed loudly instead of being cut (`text='nnnn…'`), and `show=compact` fixed it: `text='<1001 × n>'`.
- With no app, every test fails with the same clear `ModuleNotFoundError: No module named 'crm_app'`.

## Missing

1. **No spec from a red suite.** `--plainly-md` only writes after a passing run, so a test-first suite cannot show its
   reviewer the spec before the app exists, which is exactly when the review matters. Here it took a throwaway reference app.
   Idea: `--plainly-md SPEC.md --plainly-draft`, which writes the sentences of failing tests too and marks the file as not yet verified.
2. **Helper wording is not marked.** `then it has names ['Ann']` reads well, but `names` is worked out in `tests/crm.py`.
   plainly marks a hand-typed label with ✎, yet an attribute computed by a helper looks as trustworthy as a real one.
   A reviewer has to read `crm.py` to trust the spec. Idea: list the attributes that `has()` read from properties or
   helper-set fields in the hand-written-wording section, like labels.
3. **No partial match on a dict.** `has(body={...})` compares the whole body, which gives 120-character sentences.
   The way out is `expect(crm.body["id"]).should.be(2)`, which prints code (`crm.body["id"]`), uses different quotes
   from the rest of the spec, and loses the story's `then` / `and`. Ideas: `then.has_in(body, id=2)` inside stories, and
   `expect(d).should.include({"id": 2})` outside.
4. **No "comes before".** The first attempt, `expect(page.index("Ann")).should.be.less_than(page.index("Bob"))`,
   printed `... should be less than 77`: the right-hand side is evaluated before plainly sees it, so the intent was lost
   and nothing warned about it. It ended up as `should match /(?s)Ann Lee.*Bob Stone/`, which only a developer reads easily.
   Ideas: `should.list_in_order("Ann Lee", "Bob Stone")`, and a `plainly-lint` warning when a matcher's argument is a call.
5. **Repeated setup is noise.** Five list stories each start with the same three `post(...)` lines. A named setup step,
   such as `given three contacts (see three_contacts)` shown once, would make the spec shorter and easier to scan.
6. **Requests read as method calls.** `post('/api/contacts', name='Ann') is called` is clear to developers, but
   `POST /api/contacts {name: 'Ann'}` would be clearer to everyone else. A way for a story to word its own steps
   (with ✎, since the wording is then hand-written) would help HTTP and CLI apps.
7. **The width limit applies to each value, not to the sentence.** No value here was over 100 characters, but several
   sentences are 150 to 180 characters, and they are hard to read in a diff.
8. **Headings lose capitals.** `test_a_new_crm_has_no_contacts` becomes "A new crm has no contacts", and "json" stays lowercase.
