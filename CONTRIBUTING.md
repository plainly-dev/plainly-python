# Contributing to plainly

Thanks for helping. Contributions written with AI coding agents are welcome; the same rules apply to everyone,
and they are written out for agents in [AGENTS.md](AGENTS.md).

## Set up

```bash
git clone https://github.com/plainly-dev/plainly-python.git
cd plainly-python
pip install -e ".[dev]"
pytest --plainly
```

## Making a change

1. Open or pick an issue, then create a branch from `main`.
2. Make one focused change, with a test in `tests/` for any behaviour change.
3. Run `pytest` locally. If you changed how sentences are written, regenerate the affected case-study `SPEC.md` files.
4. Open a pull request. `main` is protected: CI must pass on Python 3.9 to 3.14 before merging.

In the PR description, say in plain sentences what the change promises, and call out anything it stops promising.

## If you use an AI agent

- Point it at [AGENTS.md](AGENTS.md); Claude Code reads it through [CLAUDE.md](CLAUDE.md).
- Review its tests the plainly way: run `pytest --plainly` and read the sentences, not the code.
- You are responsible for what you submit: read the diff before opening the PR.

## Reporting bugs

Open an issue with the smallest test that shows the problem, and the sentence you expected to see.
