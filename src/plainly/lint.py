"""Find checks in test files that are not written as plainly sentences.

    plainly-lint tests/                  # every test_*.py and *_test.py under tests/
    plainly-lint tests/test_cart.py      # one file (checked whatever its name)

It flags bare ``assert`` statements and ``pytest.raises``, because a reviewer
cannot read them as sentences. Write them with ``expect(...)``, ``calling(...)``,
``spec(...)`` or ``given(...)`` instead. To keep one line on purpose, end it with
``# plainly: allow``.

Exit code 1 if anything was found, 0 if not, 2 if a file could not be read.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Set

ALLOW_MARK = "# plainly: allow"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return "%s:%d:%d: %s %s" % (self.path, self.line, self.col, self.code, self.message)


ASSERT = ("PL001", "bare assert; write it as a plainly sentence, e.g. expect(x).should.be(y)")
RAISES = ("PL002", "pytest.raises; write it as calling(f, *args).should.raise_(Error)")


def is_test_file(name: str) -> bool:
    base = os.path.basename(name)
    return base.endswith(".py") and (base.startswith("test_") or base.endswith("_test.py"))


def _raises_names(tree: ast.AST) -> Set[str]:
    """Names that mean pytest.raises in this module: ``pytest`` aliases and ``from pytest import raises``."""
    modules, direct = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "pytest":
                    modules.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for a in node.names:
                if a.name == "raises":
                    direct.add(a.asname or a.name)
    return {m + ".raises" for m in modules} | direct


def _dotted(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        inner = _dotted(node.value)
        return None if inner is None else inner + "." + node.attr
    return None


def check_source(source: str, path: str = "<string>") -> List[Finding]:
    """Return the findings for one file's source text."""
    tree = ast.parse(source, filename=path)
    lines = source.splitlines()
    raises = _raises_names(tree)
    found = []
    for node in ast.walk(tree):
        rule = None
        if isinstance(node, ast.Assert):
            rule = ASSERT
        elif isinstance(node, ast.Call) and raises and _dotted(node.func) in raises:
            rule = RAISES
        if rule is None:
            continue
        text = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
        if ALLOW_MARK in text:
            continue
        found.append(Finding(path, node.lineno, node.col_offset + 1, rule[0], rule[1]))
    return sorted(found, key=lambda f: (f.line, f.col))


def iter_files(paths: Iterable[str]) -> Iterator[str]:
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "__pycache__")
                for name in sorted(files):
                    if is_test_file(name):
                        yield os.path.join(root, name)
        else:
            yield p


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="plainly-lint", description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", default=["."], help="test files or folders (default: .)")
    args = ap.parse_args(argv)
    findings, broken = [], False
    for path in iter_files(args.paths):
        try:
            with open(path, encoding="utf-8") as f:
                source = f.read()
            findings.extend(check_source(source, path))
        except (OSError, SyntaxError, UnicodeDecodeError) as e:
            sys.stderr.write("plainly-lint: cannot check %s: %s\n" % (path, e))
            broken = True
    for f in findings:
        sys.stdout.write(str(f) + "\n")
    if findings:
        sys.stdout.write("%d check(s) not written as plainly sentences\n" % len(findings))
    if broken:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
