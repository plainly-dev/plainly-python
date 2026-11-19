"""Review a change to SPEC.md: what did this pull request promise less of, or differently?

    plainly-diff --base origin/main SPEC.md              # the base version comes from git
    plainly-diff old/SPEC.md new/SPEC.md                 # or compare two files
    plainly-diff --base origin/main SPEC.md --fail-on-weakened

The report is Markdown, ready to paste into a pull request comment.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

PROSE_MARK = " ✎"


@dataclass
class Story:
    file: str
    title: str
    checks: List[str] = field(default_factory=list)  # sentences, without the ✎ mark
    hand_written: List[str] = field(default_factory=list)  # the subset that carried the mark

    @property
    def key(self) -> Tuple[str, str]:
        return (self.file, self.title)


def parse(text: str) -> Dict[Tuple[str, str], Story]:
    """Read a SPEC.md written by ``pytest --plainly-md``."""
    stories: Dict[Tuple[str, str], Story] = {}
    file, current = "", None
    for line in text.splitlines():
        if line.startswith("## "):
            file, current = line[3:].strip(), None
        elif line.startswith("### "):
            current = Story(file, line[4:].strip())
            key, n = current.key, 2
            while key in stories:  # same title twice in one file: keep both
                key = (file, f"{current.title} ({n})")
                n += 1
            current.title = key[1]
            stories[key] = current
        elif line.startswith("- ") and current is not None:
            sentence = line[2:]
            marked = sentence.endswith(PROSE_MARK)
            if marked:
                sentence = sentence[: -len(PROSE_MARK)]
                current.hand_written.append(sentence)
            current.checks.append(sentence)
    return stories


def _condition(sentence: str) -> Optional[str]:
    """The part of a sentence before its outcome, so the same situation can be matched across versions."""
    for marker in (", then ", " should "):
        if marker in sentence:
            return sentence.split(marker, 1)[0]
    return None


def _outcome(sentence: str) -> str:
    for marker in (", then ", " should "):
        if marker in sentence:
            return sentence.split(marker, 1)[1]
    return sentence


def _looser(old: str, new: str) -> Optional[str]:
    """Why the new outcome promises less than the old one, if it does."""
    if "with message containing" in old and "with message containing" not in new:
        return "no longer checks the error message"
    old_raise = re.match(r"(?:must )?(?:not )?raise (\w+)", old)
    new_raise = re.match(r"(?:must )?(?:not )?raise (\w+)", new)
    if old_raise and new_raise and old_raise.group(1) != new_raise.group(1) and new_raise.group(1) in ("Exception", "BaseException"):
        return f"raise {old_raise.group(1)} became raise {new_raise.group(1)}"
    if old.startswith("give ") and new.startswith("raise "):
        return "a returned value became an error"
    return None


@dataclass
class Change:
    file: str
    story: str
    text: str
    old: str = ""
    why: str = ""


@dataclass
class Report:
    removed_checks: List[Change] = field(default_factory=list)
    removed_stories: List[Change] = field(default_factory=list)
    looser: List[Change] = field(default_factory=list)
    changed: List[Change] = field(default_factory=list)
    new_wordings: List[Change] = field(default_factory=list)
    added: List[Change] = field(default_factory=list)
    added_stories: List[Tuple[str, List[str]]] = field(default_factory=list)  # (heading, its sentences)

    @property
    def weakened(self) -> bool:
        return bool(self.removed_checks or self.removed_stories or self.looser)


def compare(old: Dict[Tuple[str, str], Story], new: Dict[Tuple[str, str], Story]) -> Report:
    report = Report()
    new_by_checks = {tuple(sorted(s.checks)): s for s in new.values()}
    for key, story in old.items():
        if key not in new:
            renamed = new_by_checks.get(tuple(sorted(story.checks)))
            if renamed is None:
                report.removed_stories.append(Change(story.file, story.title, f"{len(story.checks)} check{'s' if len(story.checks) != 1 else ''}"))
            continue
        _compare_story(story, new[key], report)
    old_by_checks = {tuple(sorted(s.checks)) for s in old.values()}
    for key, story in new.items():
        if key not in old:
            if tuple(sorted(story.checks)) not in old_by_checks:
                report.added_stories.append(
                    (f"{story.file} › {story.title} ({len(story.checks)} check{'s' if len(story.checks) != 1 else ''})", story.checks)
                )
                for sentence in story.hand_written:
                    report.new_wordings.append(Change(story.file, story.title, sentence))
    return report


def _compare_story(old: Story, new: Story, report: Report) -> None:
    remaining = list(new.checks)
    gone: List[str] = []
    for sentence in old.checks:
        if sentence in remaining:
            remaining.remove(sentence)
        else:
            gone.append(sentence)
    by_condition: Dict[str, List[str]] = {}
    for sentence in remaining:
        condition = _condition(sentence)
        if condition is not None:
            by_condition.setdefault(condition, []).append(sentence)
    for sentence in gone:
        condition = _condition(sentence)
        partner = by_condition.get(condition, []).pop(0) if condition is not None and by_condition.get(condition) else None
        if partner is None:
            report.removed_checks.append(Change(old.file, old.title, sentence))
            continue
        remaining.remove(partner)
        why = _looser(_outcome(sentence), _outcome(partner))
        change = Change(old.file, old.title, partner, old=sentence, why=why or "")
        (report.looser if why else report.changed).append(change)
    old_wordings = set(old.hand_written)
    for sentence in remaining:
        report.added.append(Change(old.file, old.title, sentence))
        if sentence in new.hand_written and sentence not in old_wordings:
            report.new_wordings.append(Change(old.file, old.title, sentence))


def render(report: Report) -> str:
    """A Markdown pull request comment."""
    counts = [
        (len(report.removed_checks), "check removed", "checks removed"),
        (len(report.removed_stories), "story removed", "stories removed"),
        (len(report.looser), "check made looser", "checks made looser"),
        (len(report.changed), "expectation changed", "expectations changed"),
        (len(report.new_wordings), "new hand-written wording", "new hand-written wordings"),
        (len(report.added), "check added", "checks added"),
        (len(report.added_stories), "story added", "stories added"),
    ]
    summary = ", ".join(f"{n} {one if n == 1 else many}" for n, one, many in counts if n) or "no change to the spec"
    lines = ["## Spec review", "", f"**{summary}.**", ""]
    if report.weakened:
        lines += ["⚠️ **This change promises less than before.** Please confirm each removal below is intended.", ""]

    def section(title: str, changes: List[Change], show_old: bool = False):
        if not changes:
            return
        lines.extend([f"### {title}", ""])
        for c in changes:
            lines.append(f"- `{c.file}` › **{c.story}**")
            if show_old:
                lines.append(f"  - before: `{c.old}`")
                lines.append(f"  - now: `{c.text}`" + (f" — {c.why}" if c.why else ""))
            else:
                lines.append(f"  - `{c.text}`")
        lines.append("")

    section("⚠️ Removed checks", report.removed_checks)
    if report.removed_stories:
        lines += ["### ⚠️ Removed stories", ""] + [f"- `{c.file}` › **{c.story}** ({c.text})" for c in report.removed_stories] + [""]
    section("⚠️ Checks made looser", report.looser, show_old=True)
    section("Expectations changed", report.changed, show_old=True)
    section("✎ New hand-written wording (check that it says what the code does)", report.new_wordings)
    if report.added or report.added_stories:
        lines += ["<details><summary>Added</summary>", ""]
        for heading, checks in report.added_stories:
            lines += [f"- new story: {heading}"] + [f"  - `{c}`" for c in checks]
        lines += [f"- `{c.file}` › **{c.story}**: `{c.text}`" for c in report.added]
        lines += ["", "</details>", ""]
    return "\n".join(lines).rstrip() + "\n"


def _read_from_git(ref: str, path: str) -> str:
    result = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""  # not in the base: everything is new


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="plainly-diff", description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", help="HEAD (with --base) or OLD NEW")
    ap.add_argument("--base", metavar="REF", help="git ref to read the old SPEC.md from, e.g. origin/main")
    ap.add_argument("--fail-on-weakened", action="store_true", help="exit 1 if a check was removed or made looser")
    ap.add_argument("--output", metavar="FILE", help="write the report here instead of printing it")
    args = ap.parse_args(argv)
    if args.base:
        if len(args.paths) != 1:
            ap.error("with --base, give one path: the SPEC.md in your working tree")
        old_text, new_path = _read_from_git(args.base, args.paths[0]), args.paths[0]
    else:
        if len(args.paths) != 2:
            ap.error("give OLD and NEW, or use --base REF PATH")
        with open(args.paths[0], encoding="utf-8") as f:
            old_text = f.read()
        new_path = args.paths[1]
    with open(new_path, encoding="utf-8") as f:
        new_text = f.read()
    report = compare(parse(old_text), parse(new_text))
    text = render(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 1 if (args.fail_on_weakened and report.weakened) else 0


if __name__ == "__main__":
    raise SystemExit(main())
